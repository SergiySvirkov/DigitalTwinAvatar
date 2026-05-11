"""
TTS Engine - Text-to-Speech with emotional style control
Uses open-source TTS (Coqui TTS) with emotion support
"""

import os
import uuid
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

# Try to import torch/TTS, but make it optional
try:
    import torch
    # Check if CUDA is available, if not use CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        # Disable CUDA warnings
        torch.cuda.is_available = lambda: False
    import torchaudio
    import numpy as np
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    torch = None
    torchaudio = None
    np = None
    TTS = None
except Exception as e:
    # Handle CUDA initialization errors
    print(f"⚠️ TTS initialization warning: {e}")
    TTS_AVAILABLE = False
    torch = None
    torchaudio = None
    np = None
    TTS = None


class TTSEngine:
    """Text-to-Speech engine with emotional control"""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or os.getenv("TTS_MODEL_PATH", "./shared/models/tts")
        self.output_dir = "./data/audio_output"
        self.sample_rate = int(os.getenv("AUDIO_SAMPLE_RATE", "24000"))

        # Ensure directories exist
        os.makedirs(self.model_path, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        # Initialize TTS model
        self.tts_model = None
        self.tts_available = TTS_AVAILABLE

        if self.tts_available:
            self._init_model()
        else:
            print("⚠️ TTS not available - using fallback mode")

        # Emotion to style mapping
        self.emotion_styles = {
            "neutral": {"speed": 1.0, "pitch": 1.0},
            "happy": {"speed": 1.1, "pitch": 1.05},
            "sad": {"speed": 0.9, "pitch": 0.95},
            "excited": {"speed": 1.2, "pitch": 1.1},
            "calm": {"speed": 0.85, "pitch": 0.98},
            "concerned": {"speed": 0.95, "pitch": 0.97},
            "enthusiastic": {"speed": 1.15, "pitch": 1.08}
        }

        print("✅ TTS Engine initialized")

    def _init_model(self):
        """Initialize the TTS model"""
        if not TTS_AVAILABLE:
            return
        try:
            # Use Coqui TTS with a multi-speaker model that supports emotions
            # Default to English model with emotion support
            model_name = "tts_models/en/ljspeech/tacotron2-DDC"

            # Try to load a better model if available
            try:
                # Attempt to load a multi-speaker emotion-capable model
                self.tts_model = TTS(
                    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                    gpu=torch.cuda.is_available() if torch else False
                )
                print("✅ Loaded XTTS v2 model (multilingual, voice cloning)")
            except Exception as e:
                # Fallback to basic model
                self.tts_model = TTS(
                    model_name=model_name,
                    gpu=torch.cuda.is_available() if torch else False
                )
                print(f"✅ Loaded TTS model: {model_name}")

        except Exception as e:
            print(f"⚠️ Error initializing TTS model: {e}")
            self.tts_model = None

    async def generate_speech(
        self,
        text: str,
        persona_id: Optional[str] = None,
        emotion: Optional[str] = None,
        voice_sample_path: Optional[str] = None
    ) -> Optional[str]:
        """Generate speech from text with emotional styling"""
        if not self.tts_available or not self.tts_model:
            print("⚠️ TTS model not available - returning placeholder")
            # Return a placeholder path for demo purposes
            return "/audio/placeholder.wav"

        try:
            # Generate unique filename
            audio_id = str(uuid.uuid4())[:8]
            output_path = os.path.join(self.output_dir, f"tts_{audio_id}.wav")

            # Get emotion style
            style = self.emotion_styles.get(emotion, self.emotion_styles["neutral"])

            # Run TTS in thread pool to not block
            loop = asyncio.get_event_loop()

            if voice_sample_path and os.path.exists(voice_sample_path):
                # Use voice cloning if sample provided
                await loop.run_in_executor(
                    None,
                    lambda: self.tts_model.tts_to_file(
                        text=text,
                        speaker_wav=voice_sample_path,
                        language="en",
                        file_path=output_path
                    )
                )
            else:
                # Standard TTS
                await loop.run_in_executor(
                    None,
                    lambda: self.tts_model.tts_to_file(
                        text=text,
                        file_path=output_path
                    )
                )

            # Apply emotion modifications if needed
            if emotion and emotion != "neutral":
                await self._apply_emotion_style(output_path, style)

            return f"/audio/tts_{audio_id}.wav"

        except Exception as e:
            print(f"⚠️ TTS generation error: {e}")
            return None

    async def _apply_emotion_style(self, audio_path: str, style: Dict[str, float]):
        """Apply emotional styling to audio (speed/pitch adjustments)"""
        if not TTS_AVAILABLE or torch is None or torchaudio is None:
            return
        try:
            # Load audio
            waveform, sample_rate = torchaudio.load(audio_path)

            # Apply speed change
            if style["speed"] != 1.0:
                # Resample for speed change
                new_sample_rate = int(sample_rate * style["speed"])
                resampler = torchaudio.transforms.Resample(sample_rate, new_sample_rate)
                waveform = resampler(waveform)
                # Resample back to original
                resampler_back = torchaudio.transforms.Resample(new_sample_rate, sample_rate)
                waveform = resampler_back(waveform)

            # Apply pitch change
            if style["pitch"] != 1.0:
                # Simple pitch shift using resampling
                pitch_shift = style["pitch"]
                new_rate = int(sample_rate * pitch_shift)
                resampler = torchaudio.transforms.Resample(sample_rate, new_rate)
                waveform = resampler(waveform)
                resampler_back = torchaudio.transforms.Resample(new_rate, sample_rate)
                waveform = resampler_back(waveform)

            # Save modified audio
            torchaudio.save(audio_path, waveform, sample_rate)

        except Exception as e:
            print(f"⚠️ Emotion styling error: {e}")

    async def clone_voice(
        self,
        voice_sample_path: str,
        text: str,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """Clone a voice from sample and generate speech"""
        if not self.tts_available or not self.tts_model:
            return None

        try:
            if not output_path:
                audio_id = str(uuid.uuid4())[:8]
                output_path = os.path.join(self.output_dir, f"cloned_{audio_id}.wav")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.tts_model.tts_to_file(
                    text=text,
                    speaker_wav=voice_sample_path,
                    language="en",
                    file_path=output_path
                )
            )

            return output_path

        except Exception as e:
            print(f"⚠️ Voice cloning error: {e}")
            return None

    def get_available_emotions(self) -> list:
        """Get list of available emotions"""
        return list(self.emotion_styles.keys())

    async def synthesize_streaming(
        self,
        text: str,
        chunk_callback,
        emotion: Optional[str] = None
    ):
        """Stream TTS audio chunks (for real-time playback)"""
        # This is a placeholder for streaming implementation
        # Full implementation would require chunked TTS generation
        audio_url = await self.generate_speech(text, emotion=emotion)
        if audio_url:
            await chunk_callback(audio_url)
