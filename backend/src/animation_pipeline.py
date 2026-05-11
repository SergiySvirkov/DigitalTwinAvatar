"""
Animation Pipeline - Talking head generation for avatar animation
Uses LivePortrait-style approach for animating static images with audio
"""

import os
import uuid
import asyncio
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass

import numpy as np
from PIL import Image

try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    torchaudio = None
except Exception as e:
    print(f"⚠️ Animation torch import warning: {e}")
    TORCH_AVAILABLE = False
    torch = None
    torchaudio = None


@dataclass
class AnimationFrame:
    """Represents a single animation frame"""
    frame_id: str
    timestamp: float
    image_data: bytes
    lip_position: Optional[Tuple[float, float, float]] = None  # x, y, openness


class AnimationPipeline:
    """Generates talking head animations from static images"""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("ANIMATION_MODEL_PATH", "./shared/models/liveportrait")
        self.output_dir = "./data/animations"
        self.personas_dir = "./shared/personas/images"

        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.personas_dir, exist_ok=True)

        # Animation state
        self.active_animations: Dict[str, Dict[str, Any]] = {}

        # Default avatar image
        self.default_avatar = self._create_default_avatar()

        print("✅ Animation Pipeline initialized")

    def _create_default_avatar(self) -> np.ndarray:
        """Create a simple default avatar image"""
        # Create a simple gradient image as placeholder
        size = (512, 512)
        img = np.zeros((*size, 3), dtype=np.uint8)

        # Create a face-like gradient
        center_x, center_y = size[0] // 2, size[1] // 2
        for y in range(size[1]):
            for x in range(size[0]):
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                if dist < 200:
                    # Face area - skin tone
                    img[y, x] = [255, 220, 177]
                else:
                    # Background
                    img[y, x] = [100, 150, 200]

        return img

    async def generate_animation(
        self,
        text: str,
        persona_id: str,
        emotion: Optional[str] = None,
        audio_path: Optional[str] = None
    ) -> Optional[str]:
        """Generate avatar animation for given text/audio"""
        try:
            animation_id = str(uuid.uuid4())[:8]

            # Get avatar image for persona
            avatar_image = await self._get_avatar_image(persona_id)

            # If audio provided, generate lip-sync animation
            if audio_path and os.path.exists(audio_path):
                animation_path = await self._generate_lip_sync_animation(
                    avatar_image=avatar_image,
                    audio_path=audio_path,
                    animation_id=animation_id,
                    emotion=emotion
                )
            else:
                # Generate idle animation
                animation_path = await self._generate_idle_animation(
                    avatar_image=avatar_image,
                    animation_id=animation_id,
                    emotion=emotion
                )

            return animation_path

        except Exception as e:
            print(f"⚠️ Animation generation error: {e}")
            return None

    async def _get_avatar_image(self, persona_id: str) -> np.ndarray:
        """Get avatar image for a persona"""
        # Try to load persona image
        persona_image_path = os.path.join(self.personas_dir, f"{persona_id}.png")

        if os.path.exists(persona_image_path):
            try:
                img = Image.open(persona_image_path)
                return np.array(img)
            except Exception as e:
                print(f"⚠️ Error loading avatar: {e}")

        # Return default avatar
        return self.default_avatar

    async def _generate_lip_sync_animation(
        self,
        avatar_image: np.ndarray,
        audio_path: str,
        animation_id: str,
        emotion: Optional[str] = None
    ) -> str:
        """Generate lip-sync animation from audio"""
        try:
            if not TORCH_AVAILABLE or torchaudio is None:
                # Fallback: return idle animation
                return await self._generate_idle_animation(avatar_image, animation_id, emotion)

            # Load audio
            waveform, sample_rate = torchaudio.load(audio_path)

            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)

            # Get audio features for lip sync
            audio_features = self._extract_audio_features(waveform, sample_rate)

            # Generate frames
            frames = []
            fps = 30
            duration = waveform.shape[1] / sample_rate
            num_frames = int(duration * fps)

            for i in range(num_frames):
                # Get audio amplitude at this time
                time_idx = int(i / fps * sample_rate)
                if time_idx < len(audio_features):
                    amplitude = audio_features[time_idx]
                else:
                    amplitude = 0

                # Generate frame with lip movement
                frame = self._generate_frame_with_lips(
                    avatar_image=avatar_image,
                    mouth_openness=amplitude,
                    emotion=emotion
                )
                frames.append(frame)

            # Save as video
            output_path = os.path.join(self.output_dir, f"animation_{animation_id}.mp4")
            await self._save_video(frames, output_path, fps)

            return f"/animations/animation_{animation_id}.mp4"

        except Exception as e:
            print(f"⚠️ Lip sync error: {e}")
            # Return idle animation as fallback
            return await self._generate_idle_animation(avatar_image, animation_id, emotion)

    def _extract_audio_features(self, waveform: Any, sample_rate: int) -> np.ndarray:
        """Extract audio features for lip sync"""
        if not TORCH_AVAILABLE:
            return np.array([])

        # Simple amplitude envelope extraction
        window_size = int(sample_rate * 0.03)  # 30ms windows
        hop_size = int(sample_rate * 0.01)     # 10ms hop

        features = []
        for i in range(0, waveform.shape[1] - window_size, hop_size):
            window = waveform[0, i:i+window_size]
            amplitude = torch.sqrt(torch.mean(window**2)).item()
            features.append(amplitude)

        # Normalize
        features = np.array(features)
        if features.max() > 0:
            features = features / features.max()

        return features

    def _generate_frame_with_lips(
        self,
        avatar_image: np.ndarray,
        mouth_openness: float,
        emotion: Optional[str] = None
    ) -> np.ndarray:
        """Generate a single frame with lip movement"""
        # Copy avatar image
        frame = avatar_image.copy()

        # Calculate mouth position (center of face)
        h, w = frame.shape[:2]
        mouth_x = w // 2
        mouth_y = int(h * 0.65)

        # Draw mouth based on openness
        lip_height = int(20 + mouth_openness * 30)
        lip_width = 60

        # Mouth color (darker for inside, lighter for lips)
        lip_color = [150, 100, 100]  # Dark red

        # Draw simple mouth shape
        y_start = mouth_y - lip_height // 2
        y_end = mouth_y + lip_height // 2
        x_start = mouth_x - lip_width // 2
        x_end = mouth_x + lip_width // 2

        # Ensure within bounds
        y_start = max(0, y_start)
        y_end = min(h, y_end)
        x_start = max(0, x_start)
        x_end = min(w, x_end)

        # Draw mouth
        frame[y_start:y_end, x_start:x_end] = lip_color

        # Add subtle head movement based on emotion
        if emotion == "excited":
            # Slight shake
            shake = np.random.randint(-2, 3)
            frame = np.roll(frame, shake, axis=1)
        elif emotion == "calm":
            # Very subtle movement
            pass

        return frame

    async def _generate_idle_animation(
        self,
        avatar_image: np.ndarray,
        animation_id: str,
        emotion: Optional[str] = None,
        duration: float = 3.0
    ) -> str:
        """Generate idle animation with subtle movements"""
        try:
            fps = 30
            num_frames = int(duration * fps)
            frames = []

            for i in range(num_frames):
                # Subtle breathing/blinking animation
                t = i / fps

                # Breathing effect (subtle scale)
                breath = 1.0 + 0.02 * np.sin(2 * np.pi * t / 2)  # 2 second breath cycle

                # Blink effect
                blink = 1.0
                if (t % 4) > 3.8:  # Blink every 4 seconds
                    blink = 0.1

                # Generate frame
                frame = self._generate_idle_frame(
                    avatar_image=avatar_image,
                    scale=breath,
                    eye_openness=blink,
                    emotion=emotion
                )
                frames.append(frame)

            # Save as video
            output_path = os.path.join(self.output_dir, f"idle_{animation_id}.mp4")
            await self._save_video(frames, output_path, fps)

            return f"/animations/idle_{animation_id}.mp4"

        except Exception as e:
            print(f"⚠️ Idle animation error: {e}")
            return None

    def _generate_idle_frame(
        self,
        avatar_image: np.ndarray,
        scale: float,
        eye_openness: float,
        emotion: Optional[str] = None
    ) -> np.ndarray:
        """Generate a single idle frame"""
        h, w = avatar_image.shape[:2]

        # Apply subtle scaling for breathing
        new_h = int(h * scale)
        new_w = int(w * scale)

        # Resize
        img_pil = Image.fromarray(avatar_image)
        img_resized = img_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Center crop
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        img_cropped = img_resized.crop((left, top, left + w, top + h))

        frame = np.array(img_cropped)

        # Draw eyes (blink effect)
        eye_y = int(h * 0.4)
        eye_x_left = int(w * 0.35)
        eye_x_right = int(w * 0.65)
        eye_size = int(8 * eye_openness)

        if eye_size > 0:
            # Draw open eyes
            eye_color = [50, 50, 50]  # Dark color for eyes
            for eye_x in [eye_x_left, eye_x_right]:
                y_start = max(0, eye_y - eye_size)
                y_end = min(h, eye_y + eye_size)
                x_start = max(0, eye_x - eye_size)
                x_end = min(w, eye_x + eye_size)
                frame[y_start:y_end, x_start:x_end] = eye_color
        else:
            # Draw closed eyes (lines)
            line_color = [50, 50, 50]
            for eye_x in [eye_x_left, eye_x_right]:
                y = eye_y
                x_start = max(0, eye_x - 10)
                x_end = min(w, eye_x + 10)
                frame[y, x_start:x_end] = line_color

        return frame

    async def _save_video(self, frames: list, output_path: str, fps: int):
        """Save frames as video file"""
        try:
            import imageio

            # Use imageio for video writing
            writer = imageio.get_writer(output_path, fps=fps, codec='libx264')

            for frame in frames:
                writer.append_data(frame)

            writer.close()

        except Exception as e:
            print(f"⚠️ Video save error: {e}")
            # Fallback: save as image sequence
            self._save_frame_sequence(frames, output_path)

    def _save_frame_sequence(self, frames: list, base_path: str):
        """Save frames as image sequence"""
        base_dir = base_path.replace('.mp4', '_frames')
        os.makedirs(base_dir, exist_ok=True)

        for i, frame in enumerate(frames):
            img = Image.fromarray(frame)
            img.save(os.path.join(base_dir, f"frame_{i:04d}.png"))

    async def get_animation_status(self, animation_id: str) -> Dict[str, Any]:
        """Get status of an animation"""
        return self.active_animations.get(animation_id, {"status": "unknown"})

    def cleanup_old_animations(self, max_age_hours: int = 24):
        """Remove old animation files"""
        import time

        current_time = time.time()
        for filename in os.listdir(self.output_dir):
            filepath = os.path.join(self.output_dir, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_hours * 3600:
                    try:
                        os.remove(filepath)
                        print(f"🧹 Cleaned up old animation: {filename}")
                    except Exception as e:
                        print(f"⚠️ Error cleaning up {filename}: {e}")
