"""
Memory Module - ChromaDB integration for conversation history and RAG
Handles conversation persistence and retrieval-augmented generation
"""

import os
import json
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation"""
    turn_id: str
    session_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {}
        }


class MemoryModule:
    """Manages conversation history using ChromaDB for RAG"""
    
    def __init__(self, db_path: Optional[str] = None, collection_name: Optional[str] = None):
        self.db_path = db_path or os.getenv("CHROMA_DB_PATH", "./data/chromadb")
        self.collection_name = collection_name or os.getenv("CHROMA_COLLECTION_NAME", "conversation_memory")
        
        # Ensure directory exists
        os.makedirs(self.db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Use default embedding function (all-MiniLM-L6-v2)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        print(f"✅ Memory module initialized with ChromaDB at {self.db_path}")
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            print(f"✅ Loaded existing collection: {self.collection_name}")
            return collection
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Conversation history and user details"}
            )
            print(f"✅ Created new collection: {self.collection_name}")
            return collection
    
    async def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a conversation turn to memory"""
        turn_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Create document with session context
        document = f"[{role.upper()}]: {content}"
        
        # Prepare metadata
        turn_metadata = {
            "turn_id": turn_id,
            "session_id": session_id,
            "role": role,
            "timestamp": timestamp,
            "content": content,
            **(metadata or {})
        }
        
        # Add to ChromaDB
        self.collection.add(
            ids=[turn_id],
            documents=[document],
            metadatas=[turn_metadata]
        )
        
        return turn_id
    
    async def get_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        try:
            results = self.collection.get(
                where={"session_id": session_id},
                limit=limit
            )
            
            history = []
            for i, doc in enumerate(results.get("documents", [])):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                history.append({
                    "turn_id": metadata.get("turn_id"),
                    "role": metadata.get("role"),
                    "content": metadata.get("content"),
                    "timestamp": metadata.get("timestamp"),
                    "metadata": {k: v for k, v in metadata.items() 
                                  if k not in ["turn_id", "session_id", "role", "timestamp", "content"]}
                })
            
            # Sort by timestamp
            history.sort(key=lambda x: x.get("timestamp", ""))
            return history
        
        except Exception as e:
            print(f"⚠️ Error retrieving history: {e}")
            return []
    
    async def query_relevant_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Query for relevant context using semantic search"""
        try:
            # Build filter if session_id provided
            where_filter = {"session_id": session_id} if session_id else None
            
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            contexts = []
            for i, doc in enumerate(results.get("documents", [[]])[0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results.get("distances") else None
                
                contexts.append({
                    "content": metadata.get("content"),
                    "role": metadata.get("role"),
                    "timestamp": metadata.get("timestamp"),
                    "relevance_score": 1 - distance if distance is not None else None,
                    "metadata": {k: v for k, v in metadata.items() 
                                  if k not in ["turn_id", "session_id", "role", "timestamp", "content"]}
                })
            
            return contexts
        
        except Exception as e:
            print(f"⚠️ Error querying context: {e}")
            return []
    
    async def get_recent_context(
        self,
        session_id: str,
        n_turns: int = 10
    ) -> str:
        """Get recent conversation context as formatted string"""
        history = await self.get_history(session_id, limit=n_turns)
        
        if not history:
            return ""
        
        # Format as conversation
        context_lines = []
        for turn in history[-n_turns:]:
            role = "User" if turn["role"] == "user" else "Assistant"
            context_lines.append(f"{role}: {turn['content']}")
        
        return "\n".join(context_lines)
    
    async def add_user_fact(
        self,
        session_id: str,
        fact: str,
        fact_type: str = "general"
    ) -> str:
        """Store a fact about the user for personalization"""
        turn_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        document = f"[USER FACT - {fact_type.upper()}]: {fact}"
        
        metadata = {
            "turn_id": turn_id,
            "session_id": session_id,
            "role": "system",
            "fact_type": fact_type,
            "content": fact,
            "timestamp": timestamp,
            "is_user_fact": True
        }
        
        self.collection.add(
            ids=[turn_id],
            documents=[document],
            metadatas=[metadata]
        )
        
        return turn_id
    
    async def get_user_facts(
        self,
        session_id: str,
        fact_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve stored facts about a user"""
        try:
            where_filter = {
                "session_id": session_id,
                "is_user_fact": True
            }
            
            if fact_type:
                where_filter["fact_type"] = fact_type
            
            results = self.collection.get(
                where=where_filter
            )
            
            facts = []
            for i, doc in enumerate(results.get("documents", [])):
                metadata = results["metadatas"][i] if results["metadatas"] else {}
                facts.append({
                    "fact_id": metadata.get("turn_id"),
                    "fact_type": metadata.get("fact_type"),
                    "content": metadata.get("content"),
                    "timestamp": metadata.get("timestamp")
                })
            
            return facts
        
        except Exception as e:
            print(f"⚠️ Error retrieving user facts: {e}")
            return []
    
    async def clear_history(self, session_id: str) -> bool:
        """Clear all conversation history for a session"""
        try:
            # Get all IDs for this session
            results = self.collection.get(
                where={"session_id": session_id}
            )
            
            ids_to_delete = results.get("ids", [])
            
            if ids_to_delete:
                self.collection.delete(
                    ids=ids_to_delete
                )
            
            return True
        
        except Exception as e:
            print(f"⚠️ Error clearing history: {e}")
            return False
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session"""
        history = await self.get_history(session_id)
        facts = await self.get_user_facts(session_id)
        
        user_turns = [h for h in history if h["role"] == "user"]
        assistant_turns = [h for h in history if h["role"] == "assistant"]
        
        return {
            "session_id": session_id,
            "total_turns": len(history),
            "user_messages": len(user_turns),
            "assistant_messages": len(assistant_turns),
            "user_facts_stored": len(facts),
            "first_interaction": history[0]["timestamp"] if history else None,
            "last_interaction": history[-1]["timestamp"] if history else None
        }
    
    async def close(self):
        """Cleanup resources"""
        # ChromaDB persistent client doesn't need explicit close
        pass
