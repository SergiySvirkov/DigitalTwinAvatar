import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { Upload, User, Mic, FileText, Save, Trash2, Sparkles } from 'lucide-react';

const Container = styled.div`
  width: 100%;
  height: 100%;
  padding: 2rem;
  overflow-y: auto;
`;

const Header = styled.div`
  margin-bottom: 2rem;
  
  h1 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  
  p {
    color: rgba(255, 255, 255, 0.6);
    font-size: 1.1rem;
  }
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
`;

const Card = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 1.5rem;
  
  h2 {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    
    svg {
      width: 24px;
      height: 24px;
      color: #e94560;
    }
  }
`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.8);
  }
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  outline: none;
  transition: all 0.2s ease;
  
  &:focus {
    border-color: #e94560;
    background: rgba(255, 255, 255, 0.15);
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }
`;

const TextArea = styled.textarea`
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  outline: none;
  resize: vertical;
  min-height: 120px;
  font-family: inherit;
  transition: all 0.2s ease;
  
  &:focus {
    border-color: #e94560;
    background: rgba(255, 255, 255, 0.15);
  }
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }
`;

const UploadZone = styled.div`
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    border-color: #e94560;
    background: rgba(233, 69, 96, 0.05);
  }
  
  svg {
    width: 48px;
    height: 48px;
    color: rgba(255, 255, 255, 0.4);
    margin-bottom: 1rem;
  }
  
  p {
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 0.5rem;
  }
  
  span {
    color: #e94560;
    font-size: 0.9rem;
  }
`;

const Preview = styled.div`
  margin-top: 1rem;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.3);
  
  img {
    width: 100%;
    height: 200px;
    object-fit: cover;
  }
  
  audio {
    width: 100%;
    padding: 1rem;
  }
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #e94560 0%, #d63d56 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(233, 69, 96, 0.4);
  }
  
  svg {
    width: 20px;
    height: 20px;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const PersonaList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const PersonaItem = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(233, 69, 96, 0.5);
  }
`;

const PersonaAvatar = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  
  svg {
    width: 24px;
    height: 24px;
  }
`;

const PersonaInfo = styled.div`
  flex: 1;
  
  h3 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
  }
  
  p {
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.6);
  }
`;

const DeleteButton = styled.button`
  padding: 0.5rem;
  background: rgba(239, 68, 68, 0.1);
  border: none;
  border-radius: 8px;
  color: #ef4444;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:hover {
    background: rgba(239, 68, 68, 0.2);
  }
  
  svg {
    width: 20px;
    height: 20px;
  }
`;

const TraitGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-top: 1rem;
`;

const TraitSlider = styled.div`
  label {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    margin-bottom: 0.5rem;
    color: rgba(255, 255, 255, 0.7);
  }
  
  input[type="range"] {
    width: 100%;
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    outline: none;
    -webkit-appearance: none;
    
    &::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 16px;
      height: 16px;
      background: #e94560;
      border-radius: 50%;
      cursor: pointer;
    }
  }
`;

function PersonaCreator() {
  const [persona, setPersona] = useState({
    name: '',
    description: '',
    systemPrompt: '',
    image: null,
    voice: null,
    traits: {
      friendliness: 0.7,
      formality: 0.5,
      enthusiasm: 0.6,
      empathy: 0.8
    }
  });
  
  const [savedPersonas, setSavedPersonas] = useState([
    { id: 1, name: 'Friendly Assistant', description: 'A helpful, friendly AI companion' },
    { id: 2, name: 'Professional Coach', description: 'Motivational coaching persona' },
    { id: 3, name: 'Creative Storyteller', description: 'Imaginative narrative companion' }
  ]);
  
  const imageInputRef = useRef(null);
  const voiceInputRef = useRef(null);

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (event) => {
        setPersona(prev => ({ ...prev, image: event.target.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleVoiceUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setPersona(prev => ({ ...prev, voice: url }));
    }
  };

  const handleTraitChange = (trait, value) => {
    setPersona(prev => ({
      ...prev,
      traits: { ...prev.traits, [trait]: parseFloat(value) }
    }));
  };

  const handleSave = () => {
    if (!persona.name || !persona.systemPrompt) return;
    
    const newPersona = {
      id: Date.now(),
      name: persona.name,
      description: persona.description || 'Custom persona'
    };
    
    setSavedPersonas(prev => [...prev, newPersona]);
    
    // Reset form
    setPersona({
      name: '',
      description: '',
      systemPrompt: '',
      image: null,
      voice: null,
      traits: {
        friendliness: 0.7,
        formality: 0.5,
        enthusiasm: 0.6,
        empathy: 0.8
      }
    });
  };

  const handleDelete = (id) => {
    setSavedPersonas(prev => prev.filter(p => p.id !== id));
  };

  return (
    <Container>
      <Header>
        <h1><Sparkles /> Persona Creator</h1>
        <p>Create custom AI personas with unique personalities, voices, and avatars</p>
      </Header>
      
      <Grid>
        <Card>
          <h2><User /> Create New Persona</h2>
          
          <FormGroup>
            <label>Persona Name</label>
            <Input
              type="text"
              placeholder="e.g., Friendly Assistant"
              value={persona.name}
              onChange={(e) => setPersona(prev => ({ ...prev, name: e.target.value }))}
            />
          </FormGroup>
          
          <FormGroup>
            <label>Description</label>
            <Input
              type="text"
              placeholder="Brief description of this persona"
              value={persona.description}
              onChange={(e) => setPersona(prev => ({ ...prev, description: e.target.value }))}
            />
          </FormGroup>
          
          <FormGroup>
            <label>System Prompt</label>
            <TextArea
              placeholder="Define how this persona should behave..."
              value={persona.systemPrompt}
              onChange={(e) => setPersona(prev => ({ ...prev, systemPrompt: e.target.value }))}
            />
          </FormGroup>
          
          <FormGroup>
            <label>Avatar Image</label>
            <input
              type="file"
              accept="image/*"
              ref={imageInputRef}
              onChange={handleImageUpload}
              style={{ display: 'none' }}
            />
            <UploadZone onClick={() => imageInputRef.current?.click()}>
              <Upload />
              <p>Click to upload avatar image</p>
              <span>Supports JPG, PNG</span>
            </UploadZone>
            {persona.image && (
              <Preview>
                <img src={persona.image} alt="Avatar preview" />
              </Preview>
            )}
          </FormGroup>
          
          <FormGroup>
            <label>Voice Sample</label>
            <input
              type="file"
              accept="audio/*"
              ref={voiceInputRef}
              onChange={handleVoiceUpload}
              style={{ display: 'none' }}
            />
            <UploadZone onClick={() => voiceInputRef.current?.click()}>
              <Mic />
              <p>Click to upload voice sample</p>
              <span>Supports MP3, WAV</span>
            </UploadZone>
            {persona.voice && (
              <Preview>
                <audio controls src={persona.voice} />
              </Preview>
            )}
          </FormGroup>
          
          <FormGroup>
            <label>Personality Traits</label>
            <TraitGrid>
              {Object.entries(persona.traits).map(([trait, value]) => (
                <TraitSlider key={trait}>
                  <label>
                    <span>{trait.charAt(0).toUpperCase() + trait.slice(1)}</span>
                    <span>{(value * 100).toFixed(0)}%</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={value}
                    onChange={(e) => handleTraitChange(trait, e.target.value)}
                  />
                </TraitSlider>
              ))}
            </TraitGrid>
          </FormGroup>
          
          <Button 
            onClick={handleSave}
            disabled={!persona.name || !persona.systemPrompt}
          >
            <Save /> Save Persona
          </Button>
        </Card>
        
        <Card>
          <h2><FileText /> Saved Personas</h2>
          <PersonaList>
            {savedPersonas.map(p => (
              <PersonaItem key={p.id}>
                <PersonaAvatar>
                  <User />
                </PersonaAvatar>
                <PersonaInfo>
                  <h3>{p.name}</h3>
                  <p>{p.description}</p>
                </PersonaInfo>
                <DeleteButton onClick={() => handleDelete(p.id)}>
                  <Trash2 />
                </DeleteButton>
              </PersonaItem>
            ))}
          </PersonaList>
        </Card>
      </Grid>
    </Container>
  );
}

export default PersonaCreator;
