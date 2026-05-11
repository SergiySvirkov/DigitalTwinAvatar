import React, { useState, useRef, useEffect, useCallback } from 'react';
import styled from 'styled-components';
import {
  Mic, MicOff, Video as VideoIcon, VideoOff,
  PhoneOff, MessageSquare, Users, Send,
  FileText, Upload, X, CheckCircle, AlertCircle,
  Loader2
} from 'lucide-react';

// Styled Components
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

const DocumentButton = styled(ControlButton)`
  background: ${props => props.active ? 'rgba(59, 130, 246, 0.3)' : 'rgba(255, 255, 255, 0.1)'};
  border-color: ${props => props.active ? '#3b82f6' : 'transparent'};
  
  &:hover {
    background: ${props => props.active ? 'rgba(59, 130, 246, 0.4)' : 'rgba(255, 255, 255, 0.2)'};
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

// Document Upload Modal Styles
const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
`;

const ModalContent = styled.div`
  background: #1a1a2e;
  border-radius: 16px;
  padding: 2rem;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;

  h3 {
    margin: 0;
    font-size: 1.25rem;
    color: white;
  }
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    color: white;
  }

  svg {
    width: 20px;
    height: 20px;
  }
`;

const DropZone = styled.div`
  border: 2px dashed ${props => props.isDragging ? '#3b82f6' : 'rgba(255, 255, 255, 0.2)'};
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  background: ${props => props.isDragging ? 'rgba(59, 130, 246, 0.1)' : 'rgba(255, 255, 255, 0.05)'};
  transition: all 0.2s ease;
  cursor: pointer;

  &:hover {
    border-color: #3b82f6;
    background: rgba(59, 130, 246, 0.05);
  }

  svg {
    width: 48px;
    height: 48px;
    color: ${props => props.isDragging ? '#3b82f6' : 'rgba(255, 255, 255, 0.4)'};
    margin-bottom: 1rem;
    transition: all 0.2s ease;
  }

  p {
    margin: 0;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.95rem;
  }

  span {
    color: #3b82f6;
    font-weight: 500;
  }
`;

const FileInput = styled.input`
  display: none;
`;

const FilePreview = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-top: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);

  svg {
    width: 24px;
    height: 24px;
    color: #3b82f6;
  }

  .file-info {
    flex: 1;
    text-align: left;

    .filename {
      color: white;
      font-weight: 500;
      font-size: 0.9rem;
      margin-bottom: 0.25rem;
    }

    .filesize {
      color: rgba(255, 255, 255, 0.5);
      font-size: 0.8rem;
    }
  }
`;

const UploadButton = styled.button`
  width: 100%;
  padding: 0.875rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;

  &:hover:not(:disabled) {
    background: #2563eb;
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  svg {
    width: 18px;
    height: 18px;
  }
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  margin-top: 1rem;
  overflow: hidden;

  .progress {
    height: 100%;
    background: #3b82f6;
    border-radius: 2px;
    transition: width 0.3s ease;
    width: ${props => props.progress}%;`
};

// Toast Notification Styles
const ToastContainer = styled.div`
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  z-index: 1100;
`;

const Toast = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: ${props => props.type === 'success' ? 'rgba(34, 197, 94, 0.9)' : 'rgba(239, 68, 68, 0.9)'};
  border-radius: 8px;
  color: white;
  font-size: 0.9rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  animation: slideIn 0.3s ease;

  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  svg {
    width: 20px;
    height: 20px;
  }
`;

const TitleInput = styled.input`
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  margin-bottom: 1rem;
  outline: none;

  &:focus {
    border-color: #3b82f6;
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }
`;

// API Configuration
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8081';

function VideoCall({ onConnectionChange }) {
  // Existing state
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

  // Document upload state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [documentTitle, setDocumentTitle] = useState('');
  const [toasts, setToasts] = useState([]);
  const [uploadedDocuments, setUploadedDocuments] = useState([]);

  const localVideoRef = useRef(null);
  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

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

  // Toast notification helper
  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  };

  // Toggle microphone
  const toggleMic = useCallback(async () => {
    if (!isMicOn) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        setIsMicOn(true);
      } catch (err) {
        console.error('Error accessing microphone:', err);
        showToast('Could not access microphone', 'error');
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
        showToast('Could not access camera', 'error');
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

  // Document upload handlers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'application/pdf' || file.type === 'text/plain')) {
      setSelectedFile(file);
      if (!documentTitle) {
        setDocumentTitle(file.name.replace(/\.[^/.]+$/, ''));
      }
    } else {
      showToast('Only PDF and TXT files are supported', 'error');
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      if (!documentTitle) {
        setDocumentTitle(file.name.replace(/\.[^/.]+$/, ''));
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('title', documentTitle || selectedFile.name);

    try {
      const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setUploadedDocuments(prev => [...prev, result]);
        showToast(`Document "${result.metadata.title}" uploaded successfully!`);
        setShowUploadModal(false);
        setSelectedFile(null);
        setDocumentTitle('');
        setUploadProgress(100);
      } else {
        const error = await response.json();
        showToast(error.detail || 'Upload failed', 'error');
      }
    } catch (error) {
      console.error('Upload error:', error);
      showToast('Upload failed. Please try again.', 'error');
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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

        {/* Document Upload Button */}
        <DocumentButton
          active={showUploadModal}
          onClick={() => setShowUploadModal(true)}
          title="Upload Document"
        >
          <FileText />
        </DocumentButton>

        <ControlButton danger>
          <PhoneOff />
        </ControlButton>
      </ControlsBar>

      {/* Document Upload Modal */}
      {showUploadModal && (
        <ModalOverlay onClick={() => setShowUploadModal(false)}>
          <ModalContent onClick={(e) => e.stopPropagation()}>
            <ModalHeader>
              <h3>Upload Document</h3>
              <CloseButton onClick={() => setShowUploadModal(false)}>
                <X />
              </CloseButton>
            </ModalHeader>

            <TitleInput
              type="text"
              placeholder="Document title (optional)"
              value={documentTitle}
              onChange={(e) => setDocumentTitle(e.target.value)}
            />

            <DropZone
              isDragging={isDragging}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload />
              <p>
                {isDragging ? 'Drop your file here' : (
                  <>
                    Drag & drop a file here, or <span>click to browse</span>
                  </>
                )}
              </p>
              <p style={{ fontSize: '0.8rem', marginTop: '0.5rem', color: 'rgba(255,255,255,0.4)' }}>
                Supports PDF and TXT files
              </p>
            </DropZone>

            <FileInput
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt"
              onChange={handleFileSelect}
            />

            {selectedFile && (
              <FilePreview>
                <FileText />
                <div className="file-info">
                  <div className="filename">{selectedFile.name}</div>
                  <div className="filesize">{formatFileSize(selectedFile.size)}</div>
                </div>
              </FilePreview>
            )}

            {isUploading && (
              <ProgressBar progress={uploadProgress}>
                <div className="progress" />
              </ProgressBar>
            )}

            <UploadButton
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
            >
              {isUploading ? (
                <>
                  <Loader2 style={{ animation: 'spin 1s linear infinite' }} />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload />
                  Upload Document
                </>
              )}
            </UploadButton>
          </ModalContent>
        </ModalOverlay>
      )}

      {/* Toast Notifications */}
      <ToastContainer>
        {toasts.map(toast => (
          <Toast key={toast.id} type={toast.type}>
            {toast.type === 'success' ? <CheckCircle /> : <AlertCircle />}
            {toast.message}
          </Toast>
        ))}
      </ToastContainer>
    </VideoCallContainer>
  );
}

export default VideoCall;
