"""
Conversation Orchestrator - Async pipeline coordinating LLM, memory, and response generation
Manages the flow of conversation processing with low latency
"""

import os
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime

import openai
from openai import AsyncOpenAI

from .character_engine import CharacterEngine
from .memory_module import MemoryModule
from .tts_engine import TTSEngine
from .vision_processor import VisionProcessor


class ConversationOrchestrator:
    """Coordinates all conversation processing components"""
    
    def __init__(
        self,
        character_engine: CharacterEngine,
        memory_module: MemoryModule,
        tts_engine: TTSEngine,
        vision_processor: Optional[VisionProcessor] = None
    ):
        self.character_engine = character_engine
        self.memory_module = memory_module
        self.tts_engine = tts_engine
        self.vision_processor = vision_processor
        
        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.gpt_model = os.getenv("GPT_MODEL", "gpt-4o-mini")
        
        # Active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        persona_id: Optional[str] = None,
        vision_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a user message through the full pipeline"""
        start_time = datetime.utcnow()
        
        # Step 1: Store user message in memory
        await self.memory_module.add_turn(
            session_id=session_id,
            role="user",
            content=message
        )
        
        # Step 2: Gather context (parallel operations)
        context_tasks = [
            self._get_system_prompt(persona_id),
            self._get_conversation_context(session_id),
            self._get_relevant_memories(session_id, message)
        ]
        
        system_prompt, conversation_history, relevant_memories = await asyncio.gather(*context_tasks)
        
        # Step 3: Build messages for LLM
        messages = self._build_messages(
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            relevant_memories=relevant_memories,
            current_message=message,
            vision_context=vision_context
        )
        
        # Step 4: Generate LLM response
        llm_response = await self._generate_llm_response(messages)
        
        # Step 5: Detect emotion for TTS
        emotion = await self._detect_emotion(llm_response)
        
        # Step 6: Generate TTS (in background to not block)
        audio_task = asyncio.create_task(
            self.tts_engine.generate_speech(
                text=llm_response,
                persona_id=persona_id,
                emotion=emotion
            )
        )
        
        # Step 7: Store assistant response
        await self.memory_module.add_turn(
            session_id=session_id,
            role="assistant",
            content=llm_response,
            metadata={"emotion": emotion}
        )
        
        # Wait for audio generation
        audio_url = await audio_task
        
        # Calculate latency
        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        return {
            "text": llm_response,
            "audio_url": audio_url,
            "emotion": emotion,
            "latency_ms": latency_ms
        }
    
    async def _get_system_prompt(self, persona_id: Optional[str]) -> str:
        """Get system prompt for persona"""
        return self.character_engine.get_system_prompt(persona_id)
    
    async def _get_conversation_context(self, session_id: str) -> str:
        """Get recent conversation history"""
        return await self.memory_module.get_recent_context(session_id, n_turns=10)
    
    async def _get_relevant_memories(self, session_id: str, query: str) -> List[Dict[str, Any]]:
        """Query for relevant past memories"""
        return await self.memory_module.query_relevant_context(
            query=query,
            session_id=session_id,
            n_results=3
        )
    
    def _build_messages(
        self,
        system_prompt: str,
        conversation_history: str,
        relevant_memories: List[Dict[str, Any]],
        current_message: str,
        vision_context: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build message list for LLM"""
        messages = []
        
        # System prompt with context
        full_system = system_prompt
        
        # Add relevant memories to system context
        if relevant_memories:
            memory_context = "\n\nRelevant context from previous conversations:\n"
            for mem in relevant_memories:
                memory_context += f"- {mem['content']}\n"
            full_system += memory_context
        
        # Add vision context if available
        if vision_context:
            full_system += f"\n\nVisual observation: {vision_context}"
        
        messages.append({"role": "system", "content": full_system})
        
        # Add conversation history
        if conversation_history:
            # Parse and add as separate messages
            lines = conversation_history.split('\n')
            for line in lines:
                if line.startswith("User:"):
                    messages.append({
                        "role": "user",
                        "content": line[5:].strip()
                    })
                elif line.startswith("Assistant:"):
                    messages.append({
                        "role": "assistant",
                        "content": line[10:].strip()
                    })
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    async def _generate_llm_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response using OpenAI"""
        try:
            response = await self.openai_client.chat.completions.create(
                model=self.gpt_model,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                stream=False
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"⚠️ LLM generation error: {e}")
            return "I'm sorry, I'm having trouble processing your message right now. Could you try again?"
    
    async def _detect_emotion(self, text: str) -> str:
        """Detect emotion from text for TTS styling"""
        # Simple keyword-based emotion detection
        text_lower = text.lower()
        
        emotion_keywords = {
            "happy": ["happy", "joy", "excited", "great", "wonderful", "fantastic", "love", "amazing"],
            "sad": ["sad", "sorry", "unfortunate", "disappointed", "regret"],
            "excited": ["excited", "thrilled", "eager", "can't wait", "looking forward"],
            "calm": ["calm", "peaceful", "relaxed", "gentle", "soothing"],
            "concerned": ["concerned", "worried", "careful", "caution"],
            "enthusiastic": ["enthusiastic", "passionate", "energetic", "motivated"]
        }
        
        scores = {}
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[emotion] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        return "neutral"
    
    async def process_vision_frame(
        self,
        frame_data: bytes,
        session_id: str
    ) -> Optional[str]:
        """Process a vision frame and return context"""
        if not self.vision_processor:
            return None
        
        try:
            analysis = await self.vision_processor.analyze_frame(frame_data, session_id)
            return analysis
        except Exception as e:
            print(f"⚠️ Vision processing error: {e}")
            return None
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get information about a session"""
        return await self.memory_module.get_session_summary(session_id)
    
    async def clear_session(self, session_id: str):
        """Clear a session's data"""
        await self.memory_module.clear_history(session_id)
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
