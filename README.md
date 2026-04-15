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

Development requires **both** services running: backend first (so the phone has something to call), then the Flutter app on a device or emulator.

### 1. Backend (FastAPI)

**Requirements:** Python 3.11+

```bash
cd backend
python -m venv .venv
source .venv/bin/activate                  # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env                       # fill in VLM_PROVIDER + VLM_API_KEY
```

`.env` fields:

| Key | Value |
|-----|-------|
| `VLM_PROVIDER` | `gemini` / `anthropic` / `openai` |
| `VLM_API_KEY` | API key for the chosen provider |

Start the server. Use `--host 0.0.0.0` if a real phone on the same Wi-Fi needs to reach it; `127.0.0.1` is fine for emulator-only testing.

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Verify it's up:

```bash
curl http://localhost:8000/health         # or open http://localhost:8000/docs
```

Run tests:

```bash
pytest
```

### 2. Frontend (Flutter Android app)

**Requirements:** Flutter SDK (stable channel), Android Studio + Android SDK (API 24+), a physical Android device **or** an Android emulator.

```bash
cd frontend
flutter create . --org com.fchordcoach    # first time only — generates android/ native scaffold
flutter pub get
flutter devices                            # confirm your device/emulator is listed
flutter run                                # or: flutter run -d <deviceId>
```

> `hand_landmarker.task` (MediaPipe model) is already committed. No extra download.

#### Pointing the app at the backend

The backend base URL is currently hardcoded in `frontend/lib/shared/api_client.dart` as `http://localhost:8000`. `localhost` on the phone means the phone itself, not your computer, so you must choose one of:

| Scenario | What to use | How |
|----------|-------------|-----|
| **Android emulator** | `http://10.0.2.2:8000` | Edit `baseUrl` in `api_client.dart`. `10.0.2.2` is the emulator alias for the host machine. |
| **Physical phone on same Wi-Fi** | `http://<PC-LAN-IP>:8000` | Find your PC's IP (`ipconfig` on Windows, `ifconfig`/`ip addr` on macOS/Linux), e.g. `http://192.168.1.23:8000`. Make sure the backend was started with `--host 0.0.0.0` and your firewall allows inbound 8000. |
| **Physical phone via USB (no Wi-Fi routing)** | keep `http://localhost:8000` | Run `adb reverse tcp:8000 tcp:8000` once after plugging in the phone. All requests from the phone to `localhost:8000` are forwarded to your PC. |

After editing `baseUrl`, hot-restart (`R` in the `flutter run` console) — hot reload alone won't re-init `Dio`.

### 3. Verifying on a real phone

1. Enable **Developer options** → **USB debugging** on the phone.
2. Plug it in via USB; approve the RSA fingerprint prompt.
3. `flutter devices` should list the phone. If not, run `adb devices` to debug.
4. Start the backend (`uvicorn ... --host 0.0.0.0`).
5. Set `baseUrl` per the table above, then `flutter run -d <device-id>`.
6. On first launch, grant the **camera** permission when prompted.
7. Point the camera at your fretting hand forming an F chord. You should see:
   - the hand skeleton overlay (green lines, amber error joints),
   - a bottom sheet with the GNN class + VLM suggestion.
8. If the bottom sheet shows a network error, the app can't reach the backend — re-check the URL, firewall, and that `--host 0.0.0.0` was used.

Quick backend sanity check from the **phone's** browser: open `http://<PC-LAN-IP>:8000/docs`. If the Swagger UI doesn't load there, the Flutter app won't reach it either.

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
