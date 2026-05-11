import React, { useState, useRef, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import { 
  Mic, MicOff, Video as VideoIcon, VideoOff, 
  PhoneOff, MessageSquare, Users, MoreVertical,
  Send, Smile, Paperclip
} from 'lucide-react';

const VideoCallContainer = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 1rem;
  gap: 1rem;
`;

const VideoGrid = styled.div`
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  min-height: 0;
`;

const VideoContainer = styled.div`
  position: relative;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const VideoLabel = styled.div`
  position: absolute;
  top: 1rem;
  left: 1rem;
  padding: 0.5rem 1rem;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  color: white;
  z-index: 10;
`;

const VideoStatus = styled.div`
  position: absolute;
  top: 1rem;
  right: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: ${props => props.active ? 'rgba(74, 222, 128, 0.2)' : 'rgba(239, 68, 68, 0.2)'};
  border: 1px solid ${props => props.active ? '#4ade80' : '#ef4444'};
  border-radius: 8px;
  font-size: 0.8rem;
  color: ${props => props.active ? '#4ade80' : '#ef4444'};
  z-index: 10;
  
  &::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: ${props => props.active ? '#4ade80' : '#ef4444'};
    animation: ${props => props.active ? 'pulse 2s infinite' : 'none'};
  }
`;

const Video = styled.video`
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: #0a0a0a;
`;

const AvatarPlaceholder = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: rgba(255, 255, 255, 0.5);
  
  svg {
    width: 80px;
    height: 80px;
    margin-bottom: 1rem;
    opacity: 0.5;
  }
  
  span {
    font-size: 1.1rem;
  }
`;

const ChatPanel = styled.div`
  width: 350px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const ChatHeader = styled.div`
  padding: 1rem;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
  
  svg {
    width: 20px;
    height: 20px;
    color: #e94560;
  }
`;

const ChatMessages = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const Message = styled.div`
  max-width: 85%;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  font-size: 0.9rem;
  line-height: 1.4;
  
  ${props => props.fromUser ? `
    align-self: flex-end;
    background: #e94560;
    color: white;
    border-bottom-right-radius: 4px;
  ` : `
    align-self: flex-start;
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border-bottom-left-radius: 4px;
  `}
`;

const ChatInput = styled.div`
  padding: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 0.75rem;
`;

const Input = styled.input`
  flex: 1;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  outline: none;
  
  &:focus {
    border-color: #e94560;
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }
`;

const IconButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: ${props => props.primary ? '#e94560' : 'rgba(255, 255, 255, 0.1)'};
  border: none;
  border-radius: 8px;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: ${props => props.primary ? '#d63d56' : 'rgba(255, 255, 255, 0.2)'};
    transform: scale(1.05);
  }
  
  svg {
    width: 20px;
    height: 20px;
  }
`;

const ControlsBar = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 16px;
`;

const ControlButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: ${props => {
    if (props.danger) return '#ef4444';
    if (props.active) return 'rgba(255, 255, 255, 0.2)';
    return 'rgba(255, 255, 255, 0.1)';
  }};
  border: 2px solid ${props => {
    if (props.danger) return '#ef4444';
    if (props.active) return '#4ade80';
    return 'transparent';
  }};
  border-radius: 50%;
  color: white;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    transform: scale(1.1);
    background: ${props => {
      if (props.danger) return '#dc2626';
      if (props.active) return 'rgba(255, 255, 255, 0.3)';
      return 'rgba(255, 255, 255, 0.2)';
    }};
  }
  
  svg {
    width: 24px;
    height: 24px;
  }
`;

const PersonaSelector = styled.select`
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  cursor: pointer;
  outline: none;
  
  option {
    background: #1a1a2e;
    color: white;
  }
`;

const MainArea = styled.div`
  display: flex;
  gap: 1rem;
  flex: 1;
  min-height: 0;
`;

function VideoCall({ onConnectionChange }) {
  const [isMicOn, setIsMicOn] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([
    { text: "Hello! I'm your AI Digital Twin. How can I help you today?", fromUser: false }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedPersona, setSelectedPersona] = useState('default');
  const [personas, setPersonas] = useState([
    { id: 'default', name: 'Friendly Assistant' },
    { id: 'coach', name: 'Professional Coach' },
    { id: 'storyteller', name: 'Creative Storyteller' },
    { id: 'expert', name: 'Technical Expert' }
  ]);
  
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize WebSocket connection
  useEffect(() => {
    const sessionId = 'session_' + Date.now();
    const wsUrl = `ws://localhost:8081/ws/webrtc/${sessionId}`;
    
    wsRef.current = new WebSocket(wsUrl);
    
    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      onConnectionChange?.(true);
    };
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'chat_response') {
        setMessages(prev => [...prev, { text: data.response, fromUser: false }]);
      }
    };
    
    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      onConnectionChange?.(false);
    };
    
    return () => {
      wsRef.current?.close();
    };
  }, [onConnectionChange]);

  // Toggle microphone
  const toggleMic = useCallback(async () => {
    if (!isMicOn) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        setIsMicOn(true);
      } catch (err) {
        console.error('Error accessing microphone:', err);
      }
    } else {
      setIsMicOn(false);
    }
  }, [isMicOn]);

  // Toggle video
  const toggleVideo = useCallback(async () => {
    if (!isVideoOn) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }
        setIsVideoOn(true);
      } catch (err) {
        console.error('Error accessing camera:', err);
      }
    } else {
      if (localVideoRef.current?.srcObject) {
        localVideoRef.current.srcObject.getTracks().forEach(track => track.stop());
        localVideoRef.current.srcObject = null;
      }
      setIsVideoOn(false);
    }
  }, [isVideoOn]);

  // Send message
  const sendMessage = useCallback(() => {
    if (!inputMessage.trim() || !wsRef.current) return;
    
    const message = { type: 'chat', message: inputMessage, persona_id: selectedPersona };
    wsRef.current.send(JSON.stringify(message));
    
    setMessages(prev => [...prev, { text: inputMessage, fromUser: true }]);
    setInputMessage('');
  }, [inputMessage, selectedPersona]);

  // Handle key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <VideoCallContainer>
      <MainArea>
        <VideoGrid>
          <VideoContainer>
            <VideoLabel>You</VideoLabel>
            <VideoStatus active={isVideoOn}>
              {isVideoOn ? 'Camera On' : 'Camera Off'}
            </VideoStatus>
            {isVideoOn ? (
              <Video ref={localVideoRef} autoPlay muted playsInline />
            ) : (
              <AvatarPlaceholder>
                <VideoIcon />
                <span>Camera is off</span>
              </AvatarPlaceholder>
            )}
          </VideoContainer>
          
          <VideoContainer>
            <VideoLabel>AI Digital Twin</VideoLabel>
            <VideoStatus active={isConnected}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </VideoStatus>
            <AvatarPlaceholder>
              <Users />
              <span>AI Avatar</span>
            </AvatarPlaceholder>
          </VideoContainer>
        </VideoGrid>
        
        <ChatPanel>
          <ChatHeader>
            <MessageSquare />
            Chat
          </ChatHeader>
          <ChatMessages>
            {messages.map((msg, idx) => (
              <Message key={idx} fromUser={msg.fromUser}>
                {msg.text}
              </Message>
            ))}
            <div ref={messagesEndRef} />
          </ChatMessages>
          <ChatInput>
            <Input
              type="text"
              placeholder="Type a message..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <IconButton primary onClick={sendMessage}>
              <Send />
            </IconButton>
          </ChatInput>
        </ChatPanel>
      </MainArea>
      
      <ControlsBar>
        <PersonaSelector 
          value={selectedPersona}
          onChange={(e) => setSelectedPersona(e.target.value)}
        >
          {personas.map(p => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </PersonaSelector>
        
        <ControlButton 
          active={isMicOn}
          onClick={toggleMic}
        >
          {isMicOn ? <Mic /> : <MicOff />}
        </ControlButton>
        
        <ControlButton 
          active={isVideoOn}
          onClick={toggleVideo}
        >
          {isVideoOn ? <VideoIcon /> : <VideoOff />}
        </ControlButton>
        
        <ControlButton danger>
          <PhoneOff />
        </ControlButton>
      </ControlsBar>
    </VideoCallContainer>
  );
}

export default VideoCall;
