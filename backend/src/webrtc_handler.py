"""
WebRTC Handler - Manages WebRTC connections for real-time video/audio streaming
Uses aiortc for WebRTC implementation
"""

import os
import json
import asyncio
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate
from aiortc.contrib.media import MediaPlayer, MediaRecorder
from aiortc.rtcrtpsender import RTCRtpSender
from fastapi import WebSocket

from .conversation_orchestrator import ConversationOrchestrator


@dataclass
class WebRTCSession:
    """Represents an active WebRTC session"""
    session_id: str
    pc: RTCPeerConnection
    websocket: WebSocket
    audio_track: Optional = None
    video_track: Optional = None
    data_channel: Optional = None
    metadata: Dict = field(default_factory=dict)


class WebRTCHandler:
    """Handles WebRTC connections for video call"""
    
    def __init__(self, orchestrator: ConversationOrchestrator):
        self.orchestrator = orchestrator
        self.sessions: Dict[str, WebRTCSession] = {}
        
        # ICE servers configuration
        self.ice_servers = self._load_ice_servers()
        
        print("✅ WebRTC Handler initialized")
    
    def _load_ice_servers(self) -> list:
        """Load ICE servers from environment or use defaults"""
        ice_servers_env = os.getenv("RTC_ICE_SERVERS")
        
        if ice_servers_env:
            try:
                return json.loads(ice_servers_env)
            except json.JSONDecodeError:
                print("⚠️ Invalid ICE servers config, using defaults")
        
        # Default STUN servers
        return [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"}
        ]
    
    async def handle_websocket(self, websocket: WebSocket, session_id: str):
        """Handle WebSocket for WebRTC signaling"""
        await websocket.accept()
        
        # Create new RTCPeerConnection
        pc = RTCPeerConnection(configuration={"iceServers": self.ice_servers})
        
        # Create session
        session = WebRTCSession(
            session_id=session_id,
            pc=pc,
            websocket=websocket
        )
        self.sessions[session_id] = session
        
        # Setup event handlers
        self._setup_pc_handlers(session)
        
        try:
            while True:
                # Receive message from client
                message = await websocket.receive_text()
                data = json.loads(message)
                
                await self._handle_signaling_message(session, data)
        
        except Exception as e:
            print(f"⚠️ WebSocket error for session {session_id}: {e}")
        
        finally:
            # Cleanup
            await self._cleanup_session(session_id)
    
    def _setup_pc_handlers(self, session: WebRTCSession):
        """Setup RTCPeerConnection event handlers"""
        pc = session.pc
        
        @pc.on("iceconnectionstatechange")
        async def on_ice_state_change():
            print(f"ICE state for {session.session_id}: {pc.iceConnectionState}")
            if pc.iceConnectionState == "failed":
                await pc.close()
        
        @pc.on("connectionstatechange")
        async def on_connection_state_change():
            print(f"Connection state for {session.session_id}: {pc.connectionState}")
            if pc.connectionState == "failed":
                await pc.close()
        
        @pc.on("track")
        def on_track(track):
            print(f"Track received: {track.kind}")
            
            if track.kind == "audio":
                session.audio_track = track
                # Process audio track
                asyncio.create_task(self._handle_audio_track(session, track))
            
            elif track.kind == "video":
                session.video_track = track
                # Process video track
                asyncio.create_task(self._handle_video_track(session, track))
        
        @pc.on("datachannel")
        def on_datachannel(channel):
            print(f"Data channel received: {channel.label}")
            session.data_channel = channel
            
            @channel.on("message")
            def on_message(message):
                asyncio.create_task(self._handle_data_message(session, message))
    
    async def _handle_signaling_message(self, session: WebRTCSession, data: dict):
        """Handle WebRTC signaling messages"""
        msg_type = data.get("type")
        
        if msg_type == "offer":
            # Handle offer from client
            offer = RTCSessionDescription(
                sdp=data["sdp"],
                type="offer"
            )
            
            await session.pc.setRemoteDescription(offer)
            
            # Create answer
            answer = await session.pc.createAnswer()
            await session.pc.setLocalDescription(answer)
            
            # Send answer to client
            await session.websocket.send_text(json.dumps({
                "type": "answer",
                "sdp": session.pc.localDescription.sdp
            }))
        
        elif msg_type == "answer":
            # Handle answer from client
            answer = RTCSessionDescription(
                sdp=data["sdp"],
                type="answer"
            )
            await session.pc.setRemoteDescription(answer)
        
        elif msg_type == "candidate":
            # Handle ICE candidate
            candidate = RTCIceCandidate(
                sdpMLineIndex=data.get("sdpMLineIndex"),
                sdpMid=data.get("sdpMid"),
                candidate=data["candidate"]
            )
            await session.pc.addIceCandidate(candidate)
        
        elif msg_type == "chat":
            # Handle chat message
            message = data.get("message", "")
            persona_id = data.get("persona_id")
            
            # Process through orchestrator
            response = await self.orchestrator.process_message(
                message=message,
                session_id=session.session_id,
                persona_id=persona_id
            )
            
            # Send response back
            await session.websocket.send_text(json.dumps({
                "type": "chat_response",
                "response": response["text"],
                "audio_url": response.get("audio_url"),
                "emotion": response.get("emotion")
            }))
    
    async def _handle_audio_track(self, session: WebRTCSession, track):
        """Process incoming audio track"""
        try:
            while True:
                frame = await track.recv()
                # Process audio frame (e.g., for speech recognition)
                # This is where you'd integrate speech-to-text
                pass
        except Exception as e:
            print(f"⚠️ Audio track error: {e}")
    
    async def _handle_video_track(self, session: WebRTCSession, track):
        """Process incoming video track"""
        try:
            frame_count = 0
            while True:
                frame = await track.recv()
                frame_count += 1
                
                # Process every Nth frame for vision analysis
                if frame_count % 30 == 0:  # Every ~1 second at 30fps
                    # Convert frame to bytes for vision processing
                    # This is where you'd integrate vision analysis
                    pass
        
        except Exception as e:
            print(f"⚠️ Video track error: {e}")
    
    async def _handle_data_message(self, session: WebRTCSession, message: str):
        """Handle data channel messages"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "ping":
                # Respond to ping
                if session.data_channel:
                    session.data_channel.send(json.dumps({"type": "pong"}))
            
            elif msg_type == "settings":
                # Update session settings
                session.metadata.update(data.get("settings", {}))
        
        except json.JSONDecodeError:
            # Handle plain text messages
            pass
    
    async def _cleanup_session(self, session_id: str):
        """Cleanup a WebRTC session"""
        session = self.sessions.get(session_id)
        if session:
            # Close peer connection
            await session.pc.close()
            
            # Remove from sessions
            del self.sessions[session_id]
            
            print(f"🧹 Cleaned up session {session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """Send a message to a specific session"""
        session = self.sessions.get(session_id)
        if session and session.data_channel:
            session.data_channel.send(json.dumps(message))
    
    async def broadcast_message(self, message: dict):
        """Send a message to all sessions"""
        for session in self.sessions.values():
            if session.data_channel:
                session.data_channel.send(json.dumps(message))
    
    def get_session_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)
    
    async def close_all_sessions(self):
        """Close all active sessions"""
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self._cleanup_session(session_id)
