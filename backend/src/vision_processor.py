"""
Vision Processor - GPT-4o-mini or open-source VLM integration for webcam frame analysis
Processes video frames to understand visual context
"""

import os
import base64
from typing import Optional, Dict, Any
from io import BytesIO

from openai import AsyncOpenAI
from PIL import Image


class VisionProcessor:
    """Processes video frames using vision-language models"""
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("VISION_MODEL", "gpt-4o-mini")
        self.enabled = os.getenv("VISION_ENABLED", "true").lower() == "true"
        self.frame_interval = int(os.getenv("VISION_FRAME_INTERVAL", "5"))
        
        # Initialize OpenAI client
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Frame processing state
        self.last_processed_frame = {}
        self.frame_counter = {}
        
        if self.enabled:
            print(f"✅ Vision Processor initialized with {self.model}")
        else:
            print("⚠️ Vision processing disabled")
    
    async def analyze_frame(
        self,
        frame_data: bytes,
        session_id: str,
        prompt: Optional[str] = None
    ) -> Optional[str]:
        """Analyze a video frame using GPT-4o-mini"""
        if not self.enabled:
            return None
        
        try:
            # Check frame interval
            self.frame_counter[session_id] = self.frame_counter.get(session_id, 0) + 1
            if self.frame_counter[session_id] % self.frame_interval != 0:
                return None
            
            # Convert frame to base64
            base64_image = self._encode_image(frame_data)
            
            # Default prompt for conversation context
            if not prompt:
                prompt = """Describe what you see in this image briefly. Focus on:
1. The person's apparent mood/expression
2. Any notable objects or activities
3. The setting/environment
Keep it to 1-2 sentences for real-time conversation context."""
            
            # Call GPT-4o-mini with vision
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150,
                temperature=0.5
            )
            
            analysis = response.choices[0].message.content
            self.last_processed_frame[session_id] = analysis
            
            return analysis
        
        except Exception as e:
            print(f"⚠️ Vision analysis error: {e}")
            return None
    
    def _encode_image(self, image_data: bytes) -> str:
        """Encode image bytes to base64 string"""
        try:
            # Try to open and process image
            image = Image.open(BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (to reduce token usage)
            max_size = 512
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)
            
            return base64.b64encode(buffer.read()).decode('utf-8')
        
        except Exception as e:
            # Fallback: encode raw bytes
            return base64.b64encode(image_data).decode('utf-8')
    
    async def analyze_expression(
        self,
        frame_data: bytes,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Analyze facial expression for emotion detection"""
        if not self.enabled:
            return None
        
        try:
            base64_image = self._encode_image(frame_data)
            
            prompt = """Analyze the facial expression in this image. Return ONLY a JSON object with:
{
  "dominant_emotion": "happy/sad/neutral/surprised/angry/fearful/disgusted",
  "confidence": 0.0-1.0,
  "engagement_level": "high/medium/low"
}"""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=100,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
        
        except Exception as e:
            print(f"⚠️ Expression analysis error: {e}")
            return None
    
    async def detect_activity(
        self,
        frame_data: bytes,
        session_id: str
    ) -> Optional[str]:
        """Detect what activity the user is engaged in"""
        if not self.enabled:
            return None
        
        try:
            base64_image = self._encode_image(frame_data)
            
            prompt = "What activity is the person in this image doing? Answer in 3-5 words."
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=20,
                temperature=0.5
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"⚠️ Activity detection error: {e}")
            return None
    
    def get_last_analysis(self, session_id: str) -> Optional[str]:
        """Get the last frame analysis for a session"""
        return self.last_processed_frame.get(session_id)
    
    def reset_session(self, session_id: str):
        """Reset vision state for a session"""
        if session_id in self.last_processed_frame:
            del self.last_processed_frame[session_id]
        if session_id in self.frame_counter:
            del self.frame_counter[session_id]
