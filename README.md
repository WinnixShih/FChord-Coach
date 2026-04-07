# F Chord Coach

A mobile app that teaches guitar F chord fingering using real-time hand pose analysis and AI-powered feedback.

Users hold an F chord shape in front of their phone camera. The app analyzes hand posture in real time, identifies which fingers are incorrectly positioned, and provides AI-generated text suggestions for improvement.

## System Architecture

The project consists of three main components:

### Frontend (Flutter)

- Cross-platform mobile app targeting iOS and Android
- Built with Dart using the Flutter framework
- Captures camera frames and renders hand skeleton overlays via `CustomPainter`
- Communicates with the backend through REST API (`dio`)
- State management with Riverpod; local persistence with SQLite

### Backend (Python FastAPI)

- Exposes a `/infer` endpoint that accepts hand landmark data and returns analysis results as JSON
- Loads a pre-trained GNN model in ONNX format for chord posture classification
- Integrates with a Vision-Language Model API (GPT-4o or Claude) for generating natural-language suggestions
- Rate-limited to a maximum of 2 VLM calls per minute

### AI / ML

- **MediaPipe Hands** — extracts 21 hand joint landmarks (x, y, z) normalized to 0-1
- **GraphSAGE GNN** (PyTorch Geometric) — classifies F chord posture error types from joint coordinates
- Model is exported to ONNX format for inference on the backend

## Development Environment

| Component | Requirement |
|-----------|-------------|
| Frontend  | Flutter SDK (stable channel), Dart SDK |
| Backend   | Python 3.11+, FastAPI, uvicorn |
| AI / ML   | PyTorch, PyTorch Geometric, MediaPipe, ONNX Runtime |

## Project Structure

```
fchord-coach/
├── README.md
├── .gitignore
├── frontend/          # Flutter mobile app
├── backend/           # FastAPI inference server
├── ai/                # ML training, evaluation, and model export
└── docs/
    ├── api_schema.md      # API request/response contract
    └── architecture.md    # System architecture details
```
