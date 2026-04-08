# System Architecture

## Overview

```
[Phone Camera]
     │
     ▼
[Flutter App]  ──── MediaPipe Hands ────► 21 landmarks (x,y,z)
     │
     │  POST /infer  (REST)
     ▼
[FastAPI Backend]
     ├── GNN Service  ──── ONNX Runtime ───► error_type + confidence
     └── VLM Service  ──── GPT-4o / Claude ► suggestion text
```

## Components

### Frontend (Flutter)
- Captures camera frames via `camera` package
- Runs **MediaPipe Hands** on-device to extract 21 joint landmarks
- Sends landmarks to backend via `dio`
- Renders hand skeleton overlay with `CustomPainter`
- State management: Riverpod
- Local history: SQLite via `sqflite`

### Backend (FastAPI)
- `POST /infer` — main inference endpoint
- `GNNService` — loads ONNX model, classifies error type
- `VLMService` — generates natural-language suggestions, rate-limited to 2 calls/min
- Stateless; deployable as a single container

### AI / ML
- **Data**: Raw video → MediaPipe → CSV of 21×3 landmark coordinates with labels
- **Model**: GraphSAGE (2-layer) on MediaPipe hand graph topology
- **Training**: PyTorch Geometric, exported to ONNX
- **Error classes**: `correct`, `index_not_barring`, `thumb_position`, `ring_pinky_curl`, `wrist_angle`

## Data Flow

1. User holds F chord shape in front of camera
2. MediaPipe extracts 21 landmarks on-device (low latency)
3. Landmarks sent to `/infer`
4. GNN classifies error type in <50ms
5. VLM generates suggestion (rate-limited)
6. App displays skeleton overlay + text feedback
