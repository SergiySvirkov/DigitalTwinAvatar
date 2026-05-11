# Digital Twin Interaction System 🤖🎥

A high-fidelity AI Avatar Video Call system featuring real-time talking head animation, emotional text-to-speech, vision capabilities, and persistent memory.

![Digital Twin Demo](docs/demo.png)

## ✨ Features

- **🎭 Character Engine** — Flexible personality system with customizable personas (historical figures, celebrities, fictional characters)
- **🧠 Memory Module** — RAG-based conversation history using ChromaDB for persistent user interactions
- **🗣️ Emotional TTS** — Text-to-speech with style and emotion control
- **🎬 Real-time Animation** — LivePortrait-powered talking head generation with lip-sync
- **👁️ Vision Capabilities** — GPT-4o-mini integration for real-time webcam frame analysis
- **📹 Video Call Interface** — Zoom-style WebRTC interface for seamless interaction
- **🎨 Persona Creator** — Dashboard for uploading images, voice samples, and personality descriptions

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key (for vision capabilities)

### Installation

1. **Clone and setup environment:**
```bash
cd /app/digital_twin_avatar_0647
python -m venv venv
source venv/bin/activate
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and other settings
```

3. **Start the backend:**
```bash
cd backend
source ../venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8081 --reload
```

4. **Start the frontend (in a new terminal):**
```bash
cd frontend
npm install
npm start
```

5. **Access the application:**
- Frontend: http://localhost:8080
- Backend API: http://localhost:8081

## 📁 Project Structure

```
digital_twin_avatar_0647/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── src/
│   │   ├── character_engine.py # Personality & logic engine
│   │   ├── memory_module.py    # ChromaDB RAG memory
│   │   ├── conversation_orchestrator.py  # Async pipeline
│   │   ├── tts_engine.py       # Text-to-speech
│   │   ├── animation_pipeline.py  # Talking head animation
│   │   ├── vision_processor.py # GPT-4o-mini vision
│   │   └── webrtc_handler.py   # WebRTC streaming
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app component
│   │   └── components/
│   │       ├── VideoCall.jsx   # Video call interface
│   │       └── PersonaCreator.jsx  # Persona creation dashboard
│   └── package.json
├── .env.example                # Environment template
└── README.md                   # This file
```

## 🔧 Configuration

Create a `.env` file with the following variables:

```env
# OpenAI (required for vision)
OPENAI_API_KEY=your_openai_api_key_here

# Server Settings
BACKEND_PORT=8081
FRONTEND_PORT=8080
BACKEND_URL=http://localhost:8081

# Model Paths (optional - defaults will be used)
LIVEPORTRAIT_MODEL_PATH=models/LivePortrait
F5_TTS_MODEL_PATH=models/F5-TTS

# Feature Flags
ENABLE_VISION=true
ENABLE_ANIMATION=true
ENABLE_TTS=true
```

## 🎮 Usage

### Creating a Persona

1. Navigate to the **Persona Creator** tab
2. Upload a portrait image (the AI will animate this face)
3. Upload a voice sample (optional, for voice cloning)
4. Enter a personality description (system prompt)
5. Click "Create Persona"

### Starting a Video Call

1. Go to the **Video Call** tab
2. Select a persona from the dropdown
3. Allow camera/microphone access
4. Start talking to your AI avatar!

### Features During Call

- **💬 Chat** — Type or speak to the AI twin
- **🎥 Camera** — AI can see you and comment on your environment
- **🔊 Voice** — AI responds with emotional, synthesized speech
- **🎭 Expressions** — Realistic lip-sync and idle animations (blinking, head movements)
- **🧠 Memory** — AI remembers your previous conversations

## 🛠️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   React UI      │◄───►│   FastAPI        │◄───►│  Character      │
│ (Video Call)    │     │   Backend        │     │  Engine (LLM)   │
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

## 🧪 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check for all services |
| `/api/personas` | GET/POST | List or create personas |
| `/api/personas/{id}` | GET/DELETE | Get or delete a persona |
| `/api/chat` | POST | Send message to AI twin |
| `/api/vision/analyze` | POST | Analyze image with vision model |
| `/ws/signaling` | WebSocket | WebRTC signaling |

## 🐛 Troubleshooting

### Backend won't start
- Check that all Python dependencies are installed: `pip install -r backend/requirements.txt`
- Verify `.env` file exists and has required variables

### Frontend build errors
- Delete `node_modules` and run `npm install` again
- Ensure Node.js version is 18+

### Camera/microphone not working
- Ensure you're using HTTPS (or localhost for development)
- Check browser permissions for camera/microphone access

### Animation/TTS not working
- The system falls back to CPU mode if no GPU is available
- Check logs for CUDA errors (expected on CPU-only systems)

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LivePortrait](https://github.com/KwaiVGI/LivePortrait) — Real-time portrait animation
- [F5-TTS](https://github.com/SWivid/F5-TTS) — Text-to-speech with style control
- [FastRTC](https://github.com/freddyaboulton/fastrtc) — WebRTC for FastAPI
- [ChromaDB](https://github.com/chroma-core/chroma) — Vector database for RAG
- [OpenAI](https://openai.com) — GPT-4o-mini for vision capabilities

## 📧 Support

For issues and feature requests, please open an issue on the repository.

---

**Built with ❤️ for immersive AI avatar experiences**
