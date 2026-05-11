"""
DocumentRAG Module - FAISS-based document retrieval with multilingual embeddings
Supports Ukrainian, English, and 100+ languages using multilingual-e5-large model
"""

import os
import json
import uuid
import pickle
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

import faiss
from sentence_transformers import SentenceTransformer


@dataclass
class DocumentChunk:
    """Represents a chunk of a document"""
    chunk_id: str
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    chunk_index: int
    total_chunks: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "content": self.content,
            "metadata": self.metadata,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks
        }


@dataclass
class SearchResult:
    """Represents a search result"""
    chunk: DocumentChunk
    score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk": self.chunk.to_dict(),
            "score": float(self.score)
        }


class DocumentRAG:
    """
    FAISS-based document retrieval system with multilingual embeddings.
    Uses intfloat/multilingual-e5-large for state-of-the-art multilingual support.
    """
    
    def __init__(
        self,
        index_path: Optional[str] = None,
        model_name: str = "intfloat/multilingual-e5-large",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        top_k: int = 3
    ):
        """
        Initialize DocumentRAG with FAISS index and multilingual embeddings.
        
        Args:
            index_path: Path to store/load FAISS index
            model_name: Sentence transformer model for embeddings
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Overlap between chunks
            top_k: Default number of results to return
        """
        self.index_path = index_path or os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        
        # Ensure directory exists
        os.makedirs(self.index_path, exist_ok=True)
        
        # Initialize embedding model
        print(f"🔄 Loading multilingual embedding model: {model_name}")
        self.embedding_model = SentenceTransformer(model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded. Embedding dimension: {self.embedding_dim}")
        
        # Initialize or load FAISS index
        self.index_file = os.path.join(self.index_path, "faiss.index")
        self.metadata_file = os.path.join(self.index_path, "metadata.pkl")
        
        self.index = None
        self.chunks: Dict[str, DocumentChunk] = {}
        self.documents: Dict[str, Dict[str, Any]] = {}
        
        self._load_index()
        
        # Thread pool for embedding operations
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        print(f"✅ DocumentRAG initialized with FAISS at {self.index_path}")
    
    def _load_index(self):
        """Load existing FAISS index or create new one"""
        if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
            try:
                # Load FAISS index
                self.index = faiss.read_index(self.index_file)
                
                # Load metadata
                with open(self.metadata_file, 'rb') as f:
                    data = pickle.load(f)
                    self.chunks = data.get('chunks', {})
                    self.documents = data.get('documents', {})
                
                print(f"✅ Loaded existing FAISS index with {len(self.chunks)} chunks")
            except Exception as e:
                print(f"⚠️ Error loading index: {e}. Creating new index.")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index"""
        # Use IndexFlatIP for cosine similarity (normalized vectors)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        print(f"✅ Created new FAISS index (dimension: {self.embedding_dim})")
    
    def _save_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, self.index_file)
            
            # Save metadata
            with open(self.metadata_file, 'wb') as f:
                pickle.dump({
                    'chunks': self.chunks,
                    'documents': self.documents
                }, f)
            
            print(f"💾 Saved FAISS index with {len(self.chunks)} chunks")
        except Exception as e:
            print(f"⚠️ Error saving index: {e}")
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        Uses word-based chunking for multilingual support.
        """
        words = text.split()
        chunks = []
        
        if len(words) <= self.chunk_size:
            return [text]
        
        start = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            
            # Move start with overlap
            start += self.chunk_size - self.chunk_overlap
            
            # Avoid infinite loop if overlap is too large
            if start >= end:
                break
        
        return chunks
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text using multilingual model.
        For E5 models, prepend 'query:' for queries and 'passage:' for documents.
        """
        # Normalize text
        text = text.strip()
        
        # Get embedding
        embedding = self.embedding_model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        
        return embedding.astype(np.float32)
    
    async def ingest_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Ingest a document into the FAISS index.
        
        Args:
            text: Document text content
            metadata: Document metadata (title, source, language, etc.)
            doc_id: Optional document ID (generated if not provided)
            
        Returns:
            doc_id: The document ID
        """
        doc_id = doc_id or str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Prepare metadata
        doc_metadata = {
            "doc_id": doc_id,
            "timestamp": timestamp,
            "total_chunks": 0,
            **(metadata or {})
        }
        
        # Chunk the document
        chunks = self._chunk_text(text)
        doc_metadata["total_chunks"] = len(chunks)
        
        # Store document info
        self.documents[doc_id] = doc_metadata
        
        # Process chunks in thread pool
        loop = asyncio.get_event_loop()
        
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{doc_id}_{i}"
            
            # Create chunk object
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                content=chunk_text,
                metadata=doc_metadata,
                chunk_index=i,
                total_chunks=len(chunks)
            )
            
            # Get embedding (in thread pool to not block)
            embedding = await loop.run_in_executor(
                self.executor,
                self._get_embedding,
                f"passage: {chunk_text}"
            )
            
            # Add to FAISS index
            self.index.add(embedding.reshape(1, -1))
            
            # Store chunk metadata
            self.chunks[chunk_id] = chunk
        
        # Save index
        self._save_index()
        
        print(f"✅ Ingested document {doc_id} with {len(chunks)} chunks")
        return doc_id
    
    async def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        doc_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search for relevant document chunks.
        
        Args:
            query: Search query (supports Ukrainian, English, and 100+ languages)
            top_k: Number of results to return
            doc_id: Optional filter by document ID
            
        Returns:
            List of SearchResult objects
        """
        top_k = top_k or self.top_k
        
        if self.index.ntotal == 0:
            return []
        
        # Get query embedding
        loop = asyncio.get_event_loop()
        query_embedding = await loop.run_in_executor(
            self.executor,
            self._get_embedding,
            f"query: {query}"
        )
        
        # Search FAISS index
        query_embedding = query_embedding.reshape(1, -1)
        scores, indices = self.index.search(query_embedding, top_k * 2)  # Get extra for filtering
        
        # Build results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for empty slots
                continue
            
            # Get chunk by index position
            chunk_id = list(self.chunks.keys())[idx]
            chunk = self.chunks.get(chunk_id)
            
            if not chunk:
                continue
            
            # Filter by doc_id if specified
            if doc_id and chunk.doc_id != doc_id:
                continue
            
            results.append(SearchResult(chunk=chunk, score=score))
            
            if len(results) >= top_k:
                break
        
        return results
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document metadata by ID"""
        return self.documents.get(doc_id)
    
    async def get_document_chunks(self, doc_id: str) -> List[DocumentChunk]:
        """Get all chunks for a document"""
        return [
            chunk for chunk in self.chunks.values()
            if chunk.doc_id == doc_id
        ]
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document from the index.
        Note: FAISS doesn't support deletion, so we rebuild the index.
        """
        if doc_id not in self.documents:
            return False
        
        # Remove document and its chunks
        del self.documents[doc_id]
        chunks_to_remove = [
            chunk_id for chunk_id, chunk in self.chunks.items()
            if chunk.doc_id == doc_id
        ]
        
        for chunk_id in chunks_to_remove:
            del self.chunks[chunk_id]
        
        # Rebuild index (FAISS doesn't support deletion)
        if self.chunks:
            self._create_new_index()
            
            # Re-add all remaining chunks
            loop = asyncio.get_event_loop()
            for chunk in self.chunks.values():
                embedding = await loop.run_in_executor(
                    self.executor,
                    self._get_embedding,
                    f"passage: {chunk.content}"
                )
                self.index.add(embedding.reshape(1, -1))
        
        self._save_index()
        print(f"✅ Deleted document {doc_id}")
        return True
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the index"""
        return list(self.documents.values())
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        return {
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "embedding_dimension": self.embedding_dim,
            "model_name": self.model_name,
            "index_path": self.index_path
        }
    
    async def clear(self):
        """Clear all documents and reset index"""
        self.chunks.clear()
        self.documents.clear()
        self._create_new_index()
        self._save_index()
        print("✅ Cleared all documents from index")
    
    def format_context_for_llm(
        self,
        results: List[SearchResult],
        max_length: int = 2000
    ) -> str:
        """
        Format search results as context for LLM prompt.
        Includes source attribution for citations.
        """
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for result in results:
            chunk = result.chunk
            metadata = chunk.metadata
            
            # Build source citation
            source = metadata.get("title") or metadata.get("source") or f"Document {chunk.doc_id[:8]}"
            
            # Format chunk with source
            chunk_text = f"""[Source: {source}]
{chunk.content}
"""
            
            # Check length
            if current_length + len(chunk_text) > max_length:
                break
            
            context_parts.append(chunk_text)
            current_length += len(chunk_text)
        
        return "\n---\n".join(context_parts)
    
    async def close(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)
        print("✅ DocumentRAG resources cleaned up")


# Test function for verification
async def test_document_rag():
    """Test DocumentRAG with Ukrainian and English text"""
    print("\n🧪 Testing DocumentRAG Module\n")
    
    # Initialize
    rag = DocumentRAG(
        index_path="./data/test_faiss_index",
        chunk_size=100,
        chunk_overlap=20
    )
    
    # Test Ukrainian document
    ukrainian_text = """
    Привіт, як справи? Це тестовий документ українською мовою.
    Ми перевіряємо, чи працює багатомовна система пошуку.
    Українська мова має бути правильно оброблена.
    """
    
    # Test English document
    english_text = """
    Hello, how are you? This is a test document in English.
    We are checking if the multilingual search system works.
    English text should be processed correctly.
    """
    
    # Ingest documents
    print("📄 Ingesting Ukrainian document...")
    uk_doc_id = await rag.ingest_document(
        ukrainian_text,
        metadata={"title": "Ukrainian Test", "language": "uk"}
    )
    
    print("📄 Ingesting English document...")
    en_doc_id = await rag.ingest_document(
        english_text,
        metadata={"title": "English Test", "language": "en"}
    )
    
    # Test Ukrainian query
    print("\n🔍 Testing Ukrainian query...")
    uk_results = await rag.search("Привіт, як справи?", top_k=2)
    
    print(f"Query: 'Привіт, як справи?'")
    print(f"Results: {len(uk_results)}")
    
    for i, result in enumerate(uk_results):
        print(f"  {i+1}. Score: {result.score:.4f}")
        print(f"     Content: {result.chunk.content[:100]}...")
        print(f"     Source: {result.chunk.metadata.get('title', 'Unknown')}")
        
        # Verify Ukrainian document has higher score
        if i == 0:
            if result.chunk.metadata.get('language') == 'uk':
                print(f"     ✅ Correctly retrieved Ukrainian document!")
            else:
                print(f"     ⚠️ Retrieved English document instead")
    
    # Verify similarity score
    if uk_results and uk_results[0].score > 0.7:
        print(f"\n✅ PASS: Cosine similarity score {uk_results[0].score:.4f} > 0.7")
    else:
        print(f"\n❌ FAIL: Cosine similarity score too low")
    
    # Test English query
    print("\n🔍 Testing English query...")
    en_results = await rag.search("Hello, how are you?", top_k=2)
    
    print(f"Query: 'Hello, how are you?'")
    print(f"Results: {len(en_results)}")
    
    for i, result in enumerate(en_results):
        print(f"  {i+1}. Score: {result.score:.4f}")
        print(f"     Source: {result.chunk.metadata.get('title', 'Unknown')}")
    
    # Cleanup
    await rag.clear()
    print("\n✅ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_document_rag())
