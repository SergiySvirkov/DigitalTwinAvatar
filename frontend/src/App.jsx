import React, { useState } from 'react';
import styled from 'styled-components';
import VideoCall from './components/VideoCall';
import PersonaCreator from './components/PersonaCreator';
import { Users, Video, Settings } from 'lucide-react';

const AppContainer = styled.div`
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  display: flex;
  flex-direction: column;
`;

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #e94560;
  
  svg {
    width: 32px;
    height: 32px;
  }
`;

const Nav = styled.nav`
  display: flex;
  gap: 1rem;
`;

const NavButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: ${props => props.active ? '#e94560' : 'rgba(255, 255, 255, 0.1)'};
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.3s ease;
  
  &:hover {
    background: ${props => props.active ? '#d63d56' : 'rgba(255, 255, 255, 0.2)'};
    transform: translateY(-2px);
  }
  
  svg {
    width: 20px;
    height: 20px;
  }
`;

const MainContent = styled.main`
  flex: 1;
  overflow: hidden;
  position: relative;
`;

const StatusBar = styled.div`
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 0.75rem 2rem;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(10px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  
  &::before {
    content: '';
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: ${props => props.online ? '#4ade80' : '#ef4444'};
    animation: ${props => props.online ? 'pulse 2s infinite' : 'none'};
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

function App() {
  const [activeTab, setActiveTab] = useState('call');
  const [isConnected, setIsConnected] = useState(false);

  return (
    <AppContainer>
      <Header>
        <Logo>
          <Video />
          Digital Twin
        </Logo>
        <Nav>
          <NavButton 
            active={activeTab === 'call'} 
            onClick={() => setActiveTab('call')}
          >
            <Video />
            Video Call
          </NavButton>
          <NavButton 
            active={activeTab === 'personas'} 
            onClick={() => setActiveTab('personas')}
          >
            <Users />
            Personas
          </NavButton>
        </Nav>
      </Header>

      <MainContent>
        {activeTab === 'call' && (
          <VideoCall onConnectionChange={setIsConnected} />
        )}
        {activeTab === 'personas' && (
          <PersonaCreator />
        )}
      </MainContent>

      <StatusBar>
        <StatusIndicator online={isConnected}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </StatusIndicator>
        <div>
          Digital Twin v1.0.0 | WebRTC Ready
        </div>
      </StatusBar>
    </AppContainer>
  );
}

export default App;
