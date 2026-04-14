# F Chord Coach

A mobile app that teaches guitar F chord fingering using real-time hand pose analysis and AI-powered feedback.

Users hold an F chord shape in front of their phone camera. The app analyzes hand posture in real time, identifies which fingers are incorrectly positioned, and provides AI-generated text suggestions for improvement.

## System Architecture

The project consists of three main components:

### Frontend (Flutter / Android)

- Android mobile app built with Flutter + Dart
- Captures camera frames via `camera` package
- Sends frames to Kotlin via MethodChannel → MediaPipe HandLandmarker extracts 21 hand landmarks
- Communicates with the backend through REST API (`dio`)
- State management with Riverpod

### Backend (Python FastAPI)

- Exposes a `/infer` endpoint that accepts 21 hand landmark coordinates and returns analysis results
- Loads a pre-trained GNN model in ONNX format for chord posture classification
- Integrates with a Vision-Language Model API (Claude, GPT-4o, or Gemini) for generating natural-language suggestions
- Rate-limited to 2 VLM calls per minute
- CI: GitHub Actions runs backend `pytest` and `flutter analyze` on every push / PR

### AI / ML

- **MediaPipe Hands** — on-device extraction of 21 hand joint landmarks (x, y, z normalized to 0–1)
- **GraphSAGE GNN** (PyTorch Geometric) — classifies F chord posture error types from joint coordinates
- Model exported to ONNX for backend inference

## Getting Started

### Frontend

**Requirements:** Flutter SDK (stable), Android Studio, Android SDK API 24+, physical Android device or emulator

```bash
cd frontend
flutter create . --org com.fchordcoach   # generate Android native structure
flutter pub get
flutter run                               # connect an Android device or start emulator
```

> The MediaPipe model (`hand_landmarker.task`) is already included in the repo. No additional download needed.

### Backend

**Requirements:** Python 3.11+

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env    # fill in ANTHROPIC_API_KEY, OPENAI_API_KEY, or GEMINI_API_KEY
uvicorn main:app --reload
```

Run tests:

```bash
pytest
```

## Project Structure

```
fchord-coach/
├── README.md
├── DESIGN.md              # UI/UX design system (Clinical Calm)
├── frontend/              # Flutter Android app
│   ├── lib/
│   │   ├── features/      # camera, feedback pages
│   │   ├── providers/     # Riverpod state
│   │   └── services/      # API client, MediaPipe channel
│   └── android/           # Android native (Kotlin MethodChannel)
├── backend/               # FastAPI inference server
│   └── app/
│       ├── routers/       # /infer endpoint
│       └── services/      # GNNService, VLMService
├── ai/                    # ML training and ONNX export
└── docs/
    ├── api_schema.md      # API contract
    ├── architecture.md    # System architecture
    └── mediapipe-flow.md  # MediaPipe MethodChannel integration guide
```

## References

- [API Schema](docs/api_schema.md)
- [Architecture](docs/architecture.md)
- [MediaPipe Flow](docs/mediapipe-flow.md)
- [Design System](DESIGN.md)
