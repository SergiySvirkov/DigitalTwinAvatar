"""
Character Engine - Personality and System Prompt Management
Handles different personas with flexible system prompt management
"""

import os
import json
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime


class Persona:
    """Represents a single persona/character"""
    
    def __init__(
        self,
        persona_id: str,
        name: str,
        description: str,
        system_prompt: str,
        voice_sample_path: Optional[str] = None,
        image_path: Optional[str] = None,
        traits: Optional[Dict[str, Any]] = None
    ):
        self.persona_id = persona_id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.voice_sample_path = voice_sample_path
        self.image_path = image_path
        self.traits = traits or {}
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "voice_sample_path": self.voice_sample_path,
            "image_path": self.image_path,
            "traits": self.traits,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Persona':
        persona = cls(
            persona_id=data["persona_id"],
            name=data["name"],
            description=data["description"],
            system_prompt=data["system_prompt"],
            voice_sample_path=data.get("voice_sample_path"),
            image_path=data.get("image_path"),
            traits=data.get("traits", {})
        )
        persona.created_at = data.get("created_at", datetime.utcnow().isoformat())
        persona.updated_at = data.get("updated_at", datetime.utcnow().isoformat())
        return persona


class CharacterEngine:
    """Manages multiple personas and their system prompts"""
    
    def __init__(self, personas_dir: Optional[str] = None):
        self.personas_dir = personas_dir or os.getenv("PERSONAS_DIR", "./shared/personas")
        self.personas: Dict[str, Persona] = {}
        self.default_persona_id = os.getenv("DEFAULT_PERSONA", "friendly_assistant")
        
        # Ensure personas directory exists
        os.makedirs(self.personas_dir, exist_ok=True)
        
        # Load existing personas
        self._load_personas()
        
        # Create default persona if none exist
        if not self.personas:
            self._create_default_personas()
    
    def _load_personas(self):
        """Load all personas from disk"""
        personas_file = os.path.join(self.personas_dir, "personas.json")
        if os.path.exists(personas_file):
            try:
                with open(personas_file, 'r') as f:
                    data = json.load(f)
                    for persona_data in data.get("personas", []):
                        persona = Persona.from_dict(persona_data)
                        self.personas[persona.persona_id] = persona
                print(f"✅ Loaded {len(self.personas)} personas")
            except Exception as e:
                print(f"⚠️ Error loading personas: {e}")
    
    def _save_personas(self):
        """Save all personas to disk"""
        personas_file = os.path.join(self.personas_dir, "personas.json")
        try:
            data = {
                "personas": [p.to_dict() for p in self.personas.values()]
            }
            with open(personas_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving personas: {e}")
    
    def _create_default_personas(self):
        """Create default personas"""
        default_personas = [
            {
                "name": "Friendly Assistant",
                "description": "A helpful, friendly AI assistant",
                "system_prompt": """You are a friendly and helpful AI assistant. You communicate in a warm, approachable manner while being professional and informative. You enjoy helping users with their questions and tasks, and you maintain a positive, encouraging tone.""",
                "traits": {
                    "friendliness": 0.9,
                    "formality": 0.3,
                    "enthusiasm": 0.7,
                    "empathy": 0.8
                }
            },
            {
                "name": "Professional Coach",
                "description": "A motivational professional coach",
                "system_prompt": """You are a professional coach and mentor. You provide thoughtful, structured advice and encouragement. You ask insightful questions to help users discover solutions themselves. Your tone is professional yet warm, and you focus on personal growth and development.""",
                "traits": {
                    "friendliness": 0.7,
                    "formality": 0.6,
                    "enthusiasm": 0.8,
                    "empathy": 0.9
                }
            },
            {
                "name": "Creative Storyteller",
                "description": "An imaginative storyteller and creative companion",
                "system_prompt": """You are a creative storyteller with a vivid imagination. You love crafting engaging narratives, exploring ideas creatively, and bringing stories to life. Your responses are colorful, descriptive, and engaging. You enjoy wordplay and creative expression.""",
                "traits": {
                    "friendliness": 0.8,
                    "formality": 0.2,
                    "enthusiasm": 0.9,
                    "creativity": 0.95
                }
            },
            {
                "name": "Technical Expert",
                "description": "A knowledgeable technical specialist",
                "system_prompt": """You are a technical expert with deep knowledge across many domains. You provide clear, accurate, and detailed explanations. You break down complex topics into understandable parts and use precise terminology appropriately. You're patient with technical questions.""",
                "traits": {
                    "friendliness": 0.6,
                    "formality": 0.7,
                    "precision": 0.95,
                    "patience": 0.9
                }
            }
        ]
        
        for persona_data in default_personas:
            persona_id = str(uuid.uuid4())[:8]
            persona = Persona(
                persona_id=persona_id,
                name=persona_data["name"],
                description=persona_data["description"],
                system_prompt=persona_data["system_prompt"],
                traits=persona_data.get("traits", {})
            )
            self.personas[persona_id] = persona
        
        self._save_personas()
        print(f"✅ Created {len(default_personas)} default personas")
    
    async def list_personas(self) -> List[Dict[str, Any]]:
        """List all available personas"""
        return [p.to_dict() for p in self.personas.values()]
    
    async def get_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific persona by ID"""
        persona = self.personas.get(persona_id)
        return persona.to_dict() if persona else None
    
    async def create_persona(self, config: Dict[str, Any]) -> str:
        """Create a new persona"""
        persona_id = str(uuid.uuid4())[:8]
        
        persona = Persona(
            persona_id=persona_id,
            name=config["name"],
            description=config["description"],
            system_prompt=config["system_prompt"],
            voice_sample_path=config.get("voice_sample_path"),
            image_path=config.get("image_path"),
            traits=config.get("traits", {})
        )
        
        self.personas[persona_id] = persona
        self._save_personas()
        
        return persona_id
    
    async def update_persona(self, persona_id: str, config: Dict[str, Any]) -> bool:
        """Update an existing persona"""
        if persona_id not in self.personas:
            return False
        
        persona = self.personas[persona_id]
        
        if "name" in config:
            persona.name = config["name"]
        if "description" in config:
            persona.description = config["description"]
        if "system_prompt" in config:
            persona.system_prompt = config["system_prompt"]
        if "voice_sample_path" in config:
            persona.voice_sample_path = config["voice_sample_path"]
        if "image_path" in config:
            persona.image_path = config["image_path"]
        if "traits" in config:
            persona.traits.update(config["traits"])
        
        persona.updated_at = datetime.utcnow().isoformat()
        self._save_personas()
        
        return True
    
    async def delete_persona(self, persona_id: str) -> bool:
        """Delete a persona"""
        if persona_id not in self.personas:
            return False
        
        del self.personas[persona_id]
        self._save_personas()
        
        return True
    
    def get_system_prompt(self, persona_id: Optional[str] = None) -> str:
        """Get the system prompt for a persona"""
        persona_id = persona_id or self.default_persona_id
        persona = self.personas.get(persona_id)
        
        if persona:
            return persona.system_prompt
        
        # Fallback to default
        return "You are a helpful AI assistant."
    
    def get_persona_traits(self, persona_id: Optional[str] = None) -> Dict[str, Any]:
        """Get personality traits for emotion/TTS adjustment"""
        persona_id = persona_id or self.default_persona_id
        persona = self.personas.get(persona_id)
        
        if persona:
            return persona.traits
        
        return {"friendliness": 0.7, "formality": 0.5}
    
    def get_persona_image_path(self, persona_id: Optional[str] = None) -> Optional[str]:
        """Get avatar image path for a persona"""
        persona_id = persona_id or self.default_persona_id
        persona = self.personas.get(persona_id)
        
        if persona and persona.image_path and os.path.exists(persona.image_path):
            return persona.image_path
        
        return None
    
    def get_persona_voice_path(self, persona_id: Optional[str] = None) -> Optional[str]:
        """Get voice sample path for a persona"""
        persona_id = persona_id or self.default_persona_id
        persona = self.personas.get(persona_id)
        
        if persona and persona.voice_sample_path and os.path.exists(persona.voice_sample_path):
            return persona.voice_sample_path
        
        return None
