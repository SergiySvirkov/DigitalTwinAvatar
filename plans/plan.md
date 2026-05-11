# Digital Twin Interaction System (AI Avatar Video Call)

## Goal
Build a high-fidelity AI Avatar Video Call system with personality engine, emotional TTS, real-time lip-sync animation, vision capabilities, and a Zoom-style video call interface.

## Research Summary

### Talking Head Animation
- **LivePortrait (KwaiVGI/LivePortrait)**: Best quality and fast speed for portrait animation. Generates natural head movements from a single image.
- **SadTalker**: Good quality, medium speed, excellent lip sync.
- **Wav2Lip**: Industry staple, best lip sync accuracy, fast speed.
- **Decision**: Use LivePortrait for primary animation due to best overall quality and speed balance.

### Text-to-Speech (TTS)
- **F5-TTS (SWivid/F5-TTS)**: 2025 publication, supports emotional/stylistic control via prompts.
- **StyleTTS2 (yl4579/StyleTTS2)**: Established emotional speech synthesis.
- **Decision**: Use F5-TTS for emotional inflection control.

### Real-time Video Streaming
- **FastRTC**: Python library that simplifies WebRTC streaming from browser webcams with FastAPI.
- **Decision**: Use FastRTC for WebRTC implementation.

### Vision-Language Model
- **GPT-4o-mini**: Cost-efficient, supports real-time processing and streaming outputs.
- **LLaVA**: Open-source alternative.
- **Decision**: Use GPT-4o-mini for vision capabilities (requires OpenAI API key).

### Vector Database for Memory
- **ChromaDB (chromadb)**: Local, lightweight, easy to use for conversational RAG.
- **Decision**: Use ChromaDB for memory module.

## Approach

### Architecture Overview
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI        │────▶│  Character      │
│ (Video Call)    │◄────│   Backend        │◄────│  Engine (LLM)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                           │
                               ▼                           ▼
                        ┌──────────────┐           ┌──────────────┐
                        │   FastRTC    │           │  ChromaDB    │
                        │  (WebRTC)    │           │  (Memory)    │
                        └──────────────┘           └──────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐     ┌──────────┐
        │   TTS    │    │LivePortrait│    │  Vision  │
        │ (F5-TTS) │    │(Animation) │    │(GPT-4o)  │
        └──────────┘    └──────────┘     └──────────┘
```

### Key Technical Decisions
1. **Backend**: FastAPI with FastRTC for WebRTC handling
2. **Frontend**: React with WebRTC for video call interface
3. **Animation**: LivePortrait for talking head generation
4. **TTS**: F5-TTS with emotional style control
5. **Memory**: ChromaDB with conversation history embedding
6. **Vision**: GPT-4o-mini for real-time frame analysis

## Subtasks

### Phase 1: Core Infrastructure
1. **Set up project structure** — Create FastAPI backend, React frontend, and shared components directories
2. **Install dependencies** — FastRTC, ChromaDB, OpenAI client, LivePortrait, F5-TTS requirements
3. **Configure environment** — Create .env with API keys, model paths, and configuration

### Phase 2: Character Engine & Memory
4. **Build Character Engine** — Implement flexible system prompt management for different personas
5. **Implement Memory Module** — ChromaDB integration for conversation history and user details RAG
6. **Create conversation orchestrator** — Async pipeline coordinating LLM, memory retrieval, and response generation

### Phase 3: Audio Pipeline
7. **Integrate F5-TTS** — Set up TTS engine with emotional style control
8. **Build audio streaming handler** — WebRTC audio stream processing and TTS output
9. **Implement voice cloning** — Support custom voice samples for persona creation

### Phase 4: Visual Pipeline
10. **Integrate LivePortrait** — Set up talking head animation from static images
11. **Build lip-sync module** — Real-time audio-driven facial animation
12. **Add idle animations** — Subtle movements (blinking, head shifts) for natural feel
13. **Create video stream generator** — 1080p output simulation with background options

### Phase 5: Vision Capabilities
14. **Implement vision processor** — GPT-4o-mini integration for webcam frame analysis
15. **Build frame capture module** — Periodic screenshot capture from user webcam
16. **Create vision context manager** — Integrate visual observations into conversation context

### Phase 6: Web Interface
17. **Build video call UI** — React component mimicking Zoom/FaceTime interface
18. **Create Persona Creator dashboard** — Upload image, voice sample, and description interface
19. **Implement real-time streaming** — WebRTC connection between frontend and backend
20. **Add controls** — Mute, camera toggle, persona switcher, settings panel

### Phase 7: Integration & Optimization
21. **Build async pipeline coordinator** — Manage concurrent audio/video/vision processing
22. **Optimize latency** — Streaming optimizations, caching, and response time improvements
23. **Create session manager** — Handle multiple concurrent video calls and persona states

### Phase 8: Testing & Deployment
24. **Test end-to-end flow** — Full video call with persona creation and interaction
25. **Deploy services** — Start backend on port 8081, frontend on port 8080
26. **Verify accessibility** — Confirm public URLs are reachable

## Deliverables

| File Path | Description |
|-----------|-------------|
| `/app/digital_twin_avatar_0647/backend/main.py` | FastAPI backend with WebRTC endpoints |
| `/app/digital_twin_avatar_0647/backend/character_engine.py` | Personality and logic engine |
| `/app/digital_twin_avatar_0647/backend/memory.py` | ChromaDB RAG memory module |
| `/app/digital_twin_avatar_0647/backend/tts_engine.py` | F5-TTS integration |
| `/app/digital_twin_avatar_0647/backend/animation.py` | LivePortrait talking head |
| `/app/digital_twin_avatar_0647/backend/vision.py` | GPT-4o-mini vision processor |
| `/app/digital_twin_avatar_0647/frontend/src/App.jsx` | React video call interface |
| `/app/digital_twin_avatar_0647/frontend/src/components/VideoCall.jsx` | Video call component |
| `/app/digital_twin_avatar_0647/frontend/src/components/PersonaCreator.jsx` | Persona creation dashboard |
| `/app/digital_twin_avatar_0647/.env.example` | Environment configuration template |

## Evaluation Criteria
- Video call interface loads and displays properly at public URL
- Persona creation accepts image, voice sample, and description
- AI twin responds with < 2s latency for text responses
- Lip-sync animation is synchronized with audio output
- Vision capabilities process webcam frames and comment appropriately
- Memory persists across conversation turns
- Multiple personas can be created and switched between

## Notes
- Requires OpenAI API key for GPT-4o-mini vision capabilities
- LivePortrait requires GPU for real-time performance
- F5-TTS may need voice cloning training for custom voices
- WebRTC requires HTTPS for camera/microphone access
