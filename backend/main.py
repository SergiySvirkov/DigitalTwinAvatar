"""
Digital Twin Interaction System - FastAPI Backend
Main application entry point with FastRTC WebRTC integration
"""

import os
import asyncio
import json
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom modules
from src.character_engine import CharacterEngine
from src.memory_module import MemoryModule
from src.conversation_orchestrator import ConversationOrchestrator
from src.tts_engine import TTSEngine
from src.vision_processor import VisionProcessor
from src.animation_pipeline import AnimationPipeline
from src.webrtc_handler import WebRTCHandler
from src.document_rag import DocumentRAG

# Import for document processing
import io
from PyPDF2 import PdfReader

# Global instances
character_engine: Optional[CharacterEngine] = None
memory_module: Optional[MemoryModule] = None
orchestrator: Optional[ConversationOrchestrator] = None
tts_engine: Optional[TTSEngine] = None
vision_processor: Optional[VisionProcessor] = None
animation_pipeline: Optional[AnimationPipeline] = None
webrtc_handler: Optional[WebRTCHandler] = None
document_rag: Optional[DocumentRAG] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - initialize and cleanup resources"""
    global character_engine, memory_module, orchestrator, tts_engine, vision_processor, animation_pipeline, webrtc_handler, document_rag

    print("🚀 Initializing Digital Twin System...")

    # Initialize modules
    character_engine = CharacterEngine()
    memory_module = MemoryModule()
    document_rag = DocumentRAG()
    tts_engine = TTSEngine()
    vision_processor = VisionProcessor()
    animation_pipeline = AnimationPipeline()
    orchestrator = ConversationOrchestrator(
        character_engine=character_engine,
        memory_module=memory_module,
        tts_engine=tts_engine,
        vision_processor=vision_processor,
        document_rag=document_rag
    )
    webrtc_handler = WebRTCHandler(orchestrator=orchestrator)

    print("✅ All modules initialized successfully")

    yield

    # Cleanup
    print("🧹 Cleaning up resources...")
    if memory_module:
        await memory_module.close()
    if document_rag:
        await document_rag.close()
    print("✅ Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title="Digital Twin Interaction System",
    description="AI Avatar Video Call with personality engine, emotional TTS, and real-time lip-sync",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class MessageRequest(BaseModel):
    message: str = Field(..., description="User message text")
    session_id: str = Field(..., description="Unique session identifier")
    persona_id: Optional[str] = Field(None, description="Persona to use for response")

class MessageResponse(BaseModel):
    response: str = Field(..., description="AI response text")
    audio_url: Optional[str] = Field(None, description="URL to generated audio")
    emotion: Optional[str] = Field(None, description="Detected emotion")
    latency_ms: int = Field(..., description="Response generation time in milliseconds")

class PersonaConfig(BaseModel):
    name: str = Field(..., description="Persona name")
    description: str = Field(..., description="Persona description")
    system_prompt: str = Field(..., description="System prompt for the persona")
    voice_sample_path: Optional[str] = Field(None, description="Path to voice sample")
    image_path: Optional[str] = Field(None, description="Path to avatar image")
    traits: Dict[str, Any] = Field(default_factory=dict, description="Personality traits")


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "character_engine": character_engine is not None,
            "memory_module": memory_module is not None,
            "orchestrator": orchestrator is not None,
            "tts_engine": tts_engine is not None,
            "vision_processor": vision_processor is not None,
            "animation_pipeline": animation_pipeline is not None,
            "document_rag": document_rag is not None
        }
    }


# Text chat endpoint
@app.post("/api/chat", response_model=MessageResponse)
async def chat_endpoint(request: MessageRequest):
    """Main chat endpoint - processes text messages and returns AI response"""
    start_time = datetime.utcnow()

    try:
        # Process through orchestrator
        result = await orchestrator.process_message(
            message=request.message,
            session_id=request.session_id,
            persona_id=request.persona_id
        )

        # Calculate latency
        latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        return MessageResponse(
            response=result["text"],
            audio_url=result.get("audio_url"),
            emotion=result.get("emotion"),
            latency_ms=latency_ms
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


# Persona management endpoints
@app.get("/api/personas")
async def list_personas():
    """List all available personas"""
    personas = await character_engine.list_personas()
    return {"personas": personas}

@app.post("/api/personas")
async def create_persona(config: PersonaConfig):
    """Create a new persona"""
    persona_id = await character_engine.create_persona(config.dict())
    return {"persona_id": persona_id, "status": "created"}

@app.get("/api/personas/{persona_id}")
async def get_persona(persona_id: str):
    """Get persona details"""
    persona = await character_engine.get_persona(persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return persona

@app.delete("/api/personas/{persona_id}")
async def delete_persona(persona_id: str):
    """Delete a persona"""
    success = await character_engine.delete_persona(persona_id)
    if not success:
        raise HTTPException(status_code=404, detail="Persona not found")
    return {"status": "deleted"}


# File upload endpoints for persona creation
@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """Upload avatar image for persona"""
    upload_dir = "./shared/personas/images"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = f"{upload_dir}/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"image_path": file_path, "filename": file.filename}

@app.post("/api/upload/voice")
async def upload_voice(file: UploadFile = File(...)):
    """Upload voice sample for persona"""
    upload_dir = "./shared/personas/voices"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = f"{upload_dir}/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"voice_path": file_path, "filename": file.filename}


# Document upload endpoint for RAG
@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    Upload a document (PDF or TXT) for RAG retrieval.
    The document will be chunked and indexed for semantic search.
    """
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.filename.lower().endswith('.pdf'):
            # Parse PDF
            pdf_file = io.BytesIO(content)
            pdf_reader = PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        elif file.filename.lower().endswith('.txt'):
            # Parse TXT
            text = content.decode('utf-8')
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Only PDF and TXT files are supported."
            )
        
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from document."
            )
        
        # Prepare metadata
        metadata = {
            "title": title or file.filename,
            "filename": file.filename,
            "description": description or "",
            "uploaded_at": datetime.utcnow().isoformat(),
            "file_type": "pdf" if file.filename.lower().endswith('.pdf') else "txt"
        }
        
        # Ingest document into FAISS index
        doc_id = await document_rag.ingest_document(
            text=text,
            metadata=metadata
        )
        
        return {
            "doc_id": doc_id,
            "status": "success",
            "message": f"Document '{metadata['title']}' uploaded and indexed successfully",
            "metadata": metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload error: {str(e)}")


# Document management endpoints
@app.get("/api/documents")
async def list_documents():
    """List all uploaded documents"""
    try:
        documents = await document_rag.list_documents()
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get document metadata"""
    try:
        document = await document_rag.get_document(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")

@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the index"""
    try:
        success = await document_rag.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "deleted", "doc_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


# WebRTC signaling endpoint
@app.websocket("/ws/webrtc/{session_id}")
async def webrtc_websocket(websocket: WebSocket, session_id: str):
    """WebSocket for WebRTC signaling"""
    await webrtc_handler.handle_websocket(websocket, session_id)


# Vision processing endpoint
@app.post("/api/vision/analyze")
async def analyze_frame(session_id: str, file: UploadFile = File(...)):
    """Analyze a video frame for vision capabilities"""
    try:
        content = await file.read()
        analysis = await vision_processor.analyze_frame(content, session_id)
        return {"analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision analysis error: {str(e)}")


# Memory management endpoints
@app.get("/api/memory/{session_id}")
async def get_conversation_history(session_id: str, limit: int = 50):
    """Get conversation history for a session"""
    history = await memory_module.get_history(session_id, limit=limit)
    return {"history": history}

@app.delete("/api/memory/{session_id}")
async def clear_conversation_history(session_id: str):
    """Clear conversation history for a session"""
    await memory_module.clear_history(session_id)
    return {"status": "cleared"}


# Animation endpoints
@app.post("/api/animation/generate")
async def generate_animation(
    text: str = Form(...),
    persona_id: str = Form(...),
    emotion: Optional[str] = Form(None)
):
    """Generate avatar animation for text"""
    try:
        animation_url = await animation_pipeline.generate_animation(
            text=text,
            persona_id=persona_id,
            emotion=emotion
        )
        return {"animation_url": animation_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Animation error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "8081")),
        reload=True
    )
