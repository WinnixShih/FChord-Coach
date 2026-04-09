# FChord Coach Frontend & Backend MVP — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 實作 FChord Coach MVP 前後端，分三個垂直切片：(1) stub GNN + 真實 VLM 的端到端 pipeline，(2) Android Platform Channel 接 MediaPipe 真實手勢偵測，(3) 骨架 overlay UI 完整化。

**Architecture:** FastAPI 後端（GNNService stub 等 ONNX、VLMService 真實呼叫 Anthropic/OpenAI）；Flutter 前端用 Riverpod 管理狀態；Kotlin MethodChannel 包裝 Android MediaPipe SDK 提供 21 個手部 landmarks。

**Tech Stack:** Python 3.11+, FastAPI, ONNX Runtime, anthropic SDK, openai SDK, Flutter/Dart, Riverpod 2.x, camera package, Android MediaPipe Tasks Vision 0.10.14

---

## 檔案總覽

### Backend
| 動作 | 路徑 | 說明 |
|------|------|------|
| Modify | `backend/main.py` | 加 lifespan，startup 載入 GNNService |
| Modify | `backend/app/services/gnn_service.py` | 明確 `load()` 方法 + stub fallback |
| Modify | `backend/app/services/vlm_service.py` | 實作真實 Anthropic/OpenAI 呼叫 |
| Modify | `backend/requirements.txt` | 新增 `anthropic`, `openai` |
| Create | `backend/requirements-dev.txt` | pytest 依賴 |
| Create | `backend/pytest.ini` | asyncio_mode = auto |
| Create | `backend/tests/__init__.py` | 空檔，讓 tests 成為 package |
| Create | `backend/tests/test_gnn_service.py` | GNNService 單元測試 |
| Create | `backend/tests/test_vlm_service.py` | VLMService 單元測試 |
| Create | `backend/tests/test_infer_endpoint.py` | /infer 整合測試 |

### Frontend — Slice 1
| 動作 | 路徑 | 說明 |
|------|------|------|
| Modify | `frontend/lib/main.dart` | 路由到 CameraPage |
| Create | `frontend/lib/providers/infer_provider.dart` | InferResult model + AsyncNotifier |
| Modify | `frontend/lib/features/feedback/feedback_page.dart` | 顯示結果 UI |
| Modify | `frontend/lib/features/camera/camera_page.dart` | 假 landmarks 呼叫 API（Slice 1） |
| Create | `frontend/test/providers/infer_provider_test.dart` | InferResult 解析單元測試 |

### Frontend — Slice 2
| 動作 | 路徑 | 說明 |
|------|------|------|
| Modify | `frontend/android/app/build.gradle` | 加 MediaPipe dependency |
| Download | `frontend/android/app/src/main/assets/hand_landmarker.task` | MediaPipe 模型（手動下載） |
| Create | `frontend/android/app/src/main/kotlin/<pkg>/MediaPipeHandsChannel.kt` | MethodChannel 實作 |
| Modify | `frontend/android/app/src/main/kotlin/<pkg>/MainActivity.kt` | 註冊 channel |
| Modify | `frontend/lib/features/camera/camera_page.dart` | 真實相機 + Timer 分析 |

### Frontend — Slice 3
| 動作 | 路徑 | 說明 |
|------|------|------|
| Create | `frontend/lib/features/camera/hand_skeleton_painter.dart` | CustomPainter 骨架 |
| Modify | `frontend/lib/features/camera/camera_page.dart` | Stack 加 overlay |

---

## 分支規劃

| 分支 | Backlog ID | 包含 tasks |
|------|-----------|------------|
| `feat/BL-002-infer-endpoint` | BL-002 | Task 1–3 |
| `feat/BL-006-vlm-integration` | BL-006 | Task 4–5 |
| `feat/BL-005-feedback-ui` | BL-005 | Task 6–8 |
| `feat/BL-003-flutter-camera` | BL-003 | Task 9–11 |
| `feat/BL-004-hand-skeleton` | BL-004 | Task 12–13 |

---

## Slice 1 — Pipeline 跑通

### Task 1：GNNService startup load + stub fallback（BL-002）

**Branch:**
```bash
git checkout develop && git pull
git checkout -b feat/BL-002-infer-endpoint
```

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/pytest.ini`
- Create: `backend/requirements-dev.txt`
- Create: `backend/tests/test_gnn_service.py`
- Modify: `backend/app/services/gnn_service.py`

- [ ] **Step 1：建立測試基礎設施**

```bash
# 在 backend/ 目錄執行
touch backend/tests/__init__.py
```

`backend/pytest.ini`：
```ini
[pytest]
asyncio_mode = auto
```

`backend/requirements-dev.txt`：
```
pytest==8.2.0
pytest-asyncio==0.23.6
```

安裝：
```bash
cd backend
pip install -r requirements-dev.txt
```

- [ ] **Step 2：寫失敗測試**

`backend/tests/test_gnn_service.py`：
```python
import pytest
from app.services.gnn_service import GNNService


class _Lm:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


def _landmarks() -> list[_Lm]:
    return [_Lm(0.5, 0.5, 0.0) for _ in range(21)]


def test_stub_when_model_missing(tmp_path) -> None:
    svc = GNNService(model_path=str(tmp_path / "missing.onnx"))
    svc.load()
    error_type, confidence = svc.classify(_landmarks())
    assert error_type == "correct"
    assert confidence == 0.99


def test_load_does_not_raise_when_model_missing(tmp_path) -> None:
    svc = GNNService(model_path=str(tmp_path / "missing.onnx"))
    svc.load()
    assert svc._session is None
```

- [ ] **Step 3：執行測試，確認失敗**

```bash
cd backend
python -m pytest tests/test_gnn_service.py -v
```

預期：`FAILED` — `GNNService` 沒有 `load()` 方法。

- [ ] **Step 4：實作 GNNService**

`backend/app/services/gnn_service.py`：
```python
import os
import numpy as np
import onnxruntime as ort


class GNNService:
    def __init__(self, model_path: str = "models/fchord_gnn.onnx") -> None:
        self._session: ort.InferenceSession | None = None
        self._model_path = model_path

    def load(self) -> None:
        if os.path.exists(self._model_path):
            self._session = ort.InferenceSession(self._model_path)

    def classify(self, landmarks) -> tuple[str, float]:
        if self._session is None:
            return "correct", 0.99
        coords = np.array(
            [[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32
        )
        outputs = self._session.run(None, {"landmarks": coords[np.newaxis, ...]})
        error_type: str = outputs[0][0]
        confidence = float(outputs[1][0])
        return error_type, confidence
```

- [ ] **Step 5：執行測試，確認通過**

```bash
cd backend
python -m pytest tests/test_gnn_service.py -v
```

預期：`2 passed`

- [ ] **Step 6：更新 main.py 加 lifespan**

`backend/main.py`：
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import infer
from app.routers.infer import gnn_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    gnn_service.load()
    yield


app = FastAPI(title="FChord Coach API", lifespan=lifespan)
app.include_router(infer.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 7：手動驗證 server 啟動正常**

```bash
cd backend
uvicorn main:app --reload
```

預期：無 error，`GET /health` 回傳 `{"status":"ok"}`

- [ ] **Step 8：Commit**

```bash
git add backend/main.py backend/app/services/gnn_service.py \
        backend/tests/__init__.py backend/tests/test_gnn_service.py \
        backend/pytest.ini backend/requirements-dev.txt
git commit -m "feat(backend): GNNService startup load 與 stub fallback，新增測試基礎設施"
```

---

### Task 2：/infer endpoint 整合測試（BL-002）

**Files:**
- Create: `backend/tests/test_infer_endpoint.py`

- [ ] **Step 1：寫整合測試**

`backend/tests/test_infer_endpoint.py`：
```python
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _landmarks() -> list[dict[str, float]]:
    return [{"x": 0.5, "y": 0.5, "z": 0.0} for _ in range(21)]


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_infer_stub_response() -> None:
    with patch(
        "app.routers.infer.vlm_service.suggest",
        new_callable=AsyncMock,
        return_value="食指壓平，加油！",
    ):
        resp = client.post("/infer", json={"landmarks": _landmarks()})

    assert resp.status_code == 200
    data = resp.json()
    assert data["error_type"] == "correct"
    assert abs(data["confidence"] - 0.99) < 1e-6
    assert data["suggestion"] == "食指壓平，加油！"


def test_infer_rejects_missing_fields() -> None:
    resp = client.post("/infer", json={"landmarks": [{"x": 0.5} for _ in range(21)]})
    assert resp.status_code == 422
```

- [ ] **Step 2：執行，確認失敗（VLMService 尚未實作）**

```bash
cd backend
python -m pytest tests/test_infer_endpoint.py -v
```

預期：`test_infer_stub_response` 可能 pass（mock 掉 vlm），`test_health` pass，繼續即可。

- [ ] **Step 3：執行所有測試**

```bash
cd backend
python -m pytest tests/ -v
```

預期：`4 passed`

- [ ] **Step 4：Commit**

```bash
git add backend/tests/test_infer_endpoint.py
git commit -m "test(backend): 新增 /infer endpoint 整合測試"
```

---

### Task 3：VLMService 真實 API 整合（BL-006）

**Branch:**
```bash
git checkout develop
git pull
git checkout -b feat/BL-006-vlm-integration
```

> 注意：此時 BL-002 的 PR 可能尚未 merge，若需要依賴 GNNService 修改，可 branch 自 `feat/BL-002-infer-endpoint`，或等 merge 後再建立。

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/services/vlm_service.py`
- Create: `backend/tests/test_vlm_service.py`

- [ ] **Step 1：新增依賴**

`backend/requirements.txt`（在末尾加）：
```
anthropic==0.26.0
openai==1.30.0
```

```bash
cd backend
pip install anthropic openai
```

- [ ] **Step 2：寫失敗測試**

`backend/tests/test_vlm_service.py`：
```python
import time
import pytest
import app.services.vlm_service as vlm_module
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.vlm_service import VLMService


@pytest.fixture(autouse=True)
def clear_rate_limit():
    vlm_module._call_times.clear()
    yield
    vlm_module._call_times.clear()


@pytest.mark.asyncio
async def test_returns_fallback_when_rate_limited() -> None:
    vlm_module._call_times.extend([time.time(), time.time()])
    svc = VLMService()
    result = await svc.suggest("correct", [])
    assert result == "慢慢來，專注在目前的問題上，你已經很努力了！"


@pytest.mark.asyncio
async def test_suggest_delegates_to_call_vlm() -> None:
    svc = VLMService()
    with patch.object(svc, "_call_vlm", new_callable=AsyncMock, return_value="好樣的！") as mock:
        result = await svc.suggest("index_not_barring", [])
    assert result == "好樣的！"
    mock.assert_called_once_with("index_not_barring")


@pytest.mark.asyncio
async def test_call_vlm_anthropic() -> None:
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="食指壓平！")]

    with patch("anthropic.AsyncAnthropic") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        mock_client.messages.create = AsyncMock(return_value=mock_msg)

        svc = VLMService()
        svc._provider = "anthropic"
        svc._api_key = "test-key"
        result = await svc._call_vlm("index_not_barring")

    assert result == "食指壓平！"
    mock_client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_call_vlm_openai() -> None:
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="拇指位置調低！"))]

    with patch("openai.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

        svc = VLMService()
        svc._provider = "openai"
        svc._api_key = "test-key"
        result = await svc._call_vlm("thumb_position")

    assert result == "拇指位置調低！"
```

- [ ] **Step 3：執行，確認失敗**

```bash
cd backend
python -m pytest tests/test_vlm_service.py -v
```

預期：`FAILED` — `_call_vlm` 尚未真實實作。

- [ ] **Step 4：實作 VLMService**

`backend/app/services/vlm_service.py`：
```python
import os
import time
import anthropic
import openai
from dotenv import load_dotenv

load_dotenv()

_RATE_LIMIT = 2
_call_times: list[float] = []

_SYSTEM_PROMPT = "你是一位吉他老師，專門幫學生矯正 F 和弦指型。"
_USER_TEMPLATE = "學生的手型有問題：{error_type}。給一句簡短（30字以內）、鼓勵的建議。"
_FALLBACK = "慢慢來，專注在目前的問題上，你已經很努力了！"


class VLMService:
    def __init__(self) -> None:
        self._api_key = os.getenv("VLM_API_KEY", "")
        self._provider = os.getenv("VLM_PROVIDER", "anthropic")

    async def suggest(self, error_type: str, landmarks) -> str:
        if not self._can_call():
            return _FALLBACK
        _call_times.append(time.time())
        return await self._call_vlm(error_type)

    def _can_call(self) -> bool:
        now = time.time()
        recent = [t for t in _call_times if now - t < 60]
        _call_times.clear()
        _call_times.extend(recent)
        return len(recent) < _RATE_LIMIT

    async def _call_vlm(self, error_type: str) -> str:
        prompt = _USER_TEMPLATE.format(error_type=error_type)
        if self._provider == "anthropic":
            client = anthropic.AsyncAnthropic(api_key=self._api_key)
            msg = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=100,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        client = openai.AsyncOpenAI(api_key=self._api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=100,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content
```

- [ ] **Step 5：執行，確認通過**

```bash
cd backend
python -m pytest tests/ -v
```

預期：全部 pass（`test_gnn_service`、`test_vlm_service`、`test_infer_endpoint`）

- [ ] **Step 6：建立 .env.example 確認環境變數文件正確**

確認 `backend/.env.example` 包含：
```
VLM_API_KEY=your_api_key_here
VLM_PROVIDER=anthropic
```

若缺少，新增上述兩行。

- [ ] **Step 7：Commit**

```bash
git add backend/app/services/vlm_service.py backend/requirements.txt \
        backend/tests/test_vlm_service.py backend/.env.example
git commit -m "feat(backend): VLMService 整合 Anthropic/OpenAI 真實 API 呼叫"
```

---

### Task 4：Flutter InferResult model + InferNotifier（BL-005）

**Branch:**
```bash
git checkout develop && git pull
git checkout -b feat/BL-005-feedback-ui
```

**Files:**
- Create: `frontend/lib/providers/infer_provider.dart`
- Create: `frontend/test/providers/infer_provider_test.dart`

- [ ] **Step 1：寫失敗測試**

`frontend/test/providers/infer_provider_test.dart`：
```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:fchord_coach/providers/infer_provider.dart';

void main() {
  group('InferResult.fromJson', () {
    test('parses all fields correctly', () {
      final result = InferResult.fromJson({
        'error_type': 'index_not_barring',
        'confidence': 0.91,
        'suggestion': '食指壓平！',
      });
      expect(result.errorType, 'index_not_barring');
      expect(result.confidence, closeTo(0.91, 1e-6));
      expect(result.suggestion, '食指壓平！');
    });

    test('handles integer confidence', () {
      final result = InferResult.fromJson({
        'error_type': 'correct',
        'confidence': 1,
        'suggestion': '很棒！',
      });
      expect(result.confidence, 1.0);
    });
  });
}
```

- [ ] **Step 2：執行，確認失敗**

```bash
cd frontend
flutter test test/providers/infer_provider_test.dart
```

預期：`FAILED` — `InferResult` 不存在。

- [ ] **Step 3：實作 infer_provider.dart**

`frontend/lib/providers/infer_provider.dart`：
```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../shared/api_client.dart';

class InferResult {
  final String errorType;
  final double confidence;
  final String suggestion;

  const InferResult({
    required this.errorType,
    required this.confidence,
    required this.suggestion,
  });

  factory InferResult.fromJson(Map<String, dynamic> json) => InferResult(
        errorType: json['error_type'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        suggestion: json['suggestion'] as String,
      );
}

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

class InferNotifier extends AsyncNotifier<InferResult?> {
  @override
  Future<InferResult?> build() async => null;

  Future<void> infer(List<Map<String, double>> landmarks) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final json = await ref.read(apiClientProvider).infer(landmarks);
      return InferResult.fromJson(json);
    });
  }
}

final inferProvider = AsyncNotifierProvider<InferNotifier, InferResult?>(
  InferNotifier.new,
);
```

- [ ] **Step 4：執行，確認通過**

```bash
cd frontend
flutter test test/providers/infer_provider_test.dart
```

預期：`All tests passed!`

- [ ] **Step 5：Commit**

```bash
git add frontend/lib/providers/infer_provider.dart \
        frontend/test/providers/infer_provider_test.dart
git commit -m "feat(frontend): 新增 InferResult model 與 InferNotifier provider"
```

---

### Task 5：FeedbackPage UI + main.dart 路由（BL-005）

**Files:**
- Modify: `frontend/lib/main.dart`
- Modify: `frontend/lib/features/feedback/feedback_page.dart`

- [ ] **Step 1：更新 main.dart 路由到 CameraPage**

`frontend/lib/main.dart`：
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'features/camera/camera_page.dart';

void main() {
  runApp(const ProviderScope(child: FChordCoachApp()));
}

class FChordCoachApp extends StatelessWidget {
  const FChordCoachApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'F Chord Coach',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const CameraPage(),
    );
  }
}
```

- [ ] **Step 2：實作 FeedbackPage**

`frontend/lib/features/feedback/feedback_page.dart`：
```dart
import 'package:flutter/material.dart';
import '../../providers/infer_provider.dart';

class FeedbackPage extends StatelessWidget {
  final InferResult result;

  const FeedbackPage({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              _errorLabel(result.errorType),
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: result.confidence,
              backgroundColor: Colors.grey[300],
            ),
            Text(
              '信心度：${(result.confidence * 100).toStringAsFixed(0)}%',
              style: theme.textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            Text(result.suggestion, style: theme.textTheme.bodyMedium),
          ],
        ),
      ),
    );
  }

  String _errorLabel(String errorType) => switch (errorType) {
        'correct' => '手型正確',
        'index_not_barring' => '食指未橫壓',
        'thumb_position' => '拇指位置不對',
        'ring_pinky_curl' => '無名指/小指未彎曲',
        'wrist_angle' => '手腕角度不對',
        _ => errorType,
      };
}
```

- [ ] **Step 3：flutter analyze 確認無錯誤**

```bash
cd frontend
flutter analyze lib/
```

預期：`No issues found!`

- [ ] **Step 4：Commit**

```bash
git add frontend/lib/main.dart frontend/lib/features/feedback/feedback_page.dart
git commit -m "feat(frontend): 更新路由並實作 FeedbackPage 顯示推論結果"
```

---

### Task 6：CameraPage Slice 1（假 landmarks 驅動 API）（BL-005）

**Files:**
- Modify: `frontend/lib/features/camera/camera_page.dart`

- [ ] **Step 1：實作 CameraPage（Slice 1，假 landmarks）**

`frontend/lib/features/camera/camera_page.dart`：
```dart
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/infer_provider.dart';
import '../feedback/feedback_page.dart';

class CameraPage extends ConsumerWidget {
  const CameraPage({super.key});

  static final _fakeLandmarks = List.generate(
    21,
    (_) => <String, double>{'x': 0.5, 'y': 0.5, 'z': 0.0},
  );

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final inferState = ref.watch(inferProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('F Chord Coach')),
      body: SingleChildScrollView(
        child: Column(
          children: [
            Container(
              height: 300,
              color: Colors.black,
              child: const Center(
                child: Text(
                  '相機預覽（Slice 2 實作）',
                  style: TextStyle(color: Colors.white54),
                ),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: inferState.isLoading
                  ? null
                  : () =>
                      ref.read(inferProvider.notifier).infer(_fakeLandmarks),
              child: inferState.isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('分析（假 landmarks）'),
            ),
            inferState.when(
              data: (result) =>
                  result != null ? FeedbackPage(result: result) : const SizedBox.shrink(),
              loading: () => const Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ),
              error: (e, _) => Padding(
                padding: const EdgeInsets.all(16),
                child: Text('錯誤：$e',
                    style: const TextStyle(color: Colors.red)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

- [ ] **Step 2：確保後端在執行（另一個 terminal）**

```bash
cd backend
uvicorn main:app --reload
```

- [ ] **Step 3：在 Android 模擬器或實機執行 App**

```bash
cd frontend
flutter run
```

點擊「分析（假 landmarks）」按鈕，確認 FeedbackPage 顯示結果（需後端執行中，且有 VLM_API_KEY）。

- [ ] **Step 4：flutter analyze**

```bash
cd frontend
flutter analyze lib/
```

預期：`No issues found!`

- [ ] **Step 5：Commit**

```bash
git add frontend/lib/features/camera/camera_page.dart
git commit -m "feat(frontend): CameraPage Slice 1 — 假 landmarks 驅動 /infer 並顯示結果"
```

---

## Slice 2 — MediaPipe 接入

### Task 7：Android MediaPipe 環境設定（BL-003）

**Branch:**
```bash
git checkout develop && git pull
git checkout -b feat/BL-003-flutter-camera
```

**Files:**
- Modify: `frontend/android/app/build.gradle`
- Download: `frontend/android/app/src/main/assets/hand_landmarker.task`

- [ ] **Step 1：確認 Android package name**

查看 `frontend/android/app/build.gradle`，找到 `applicationId`，記下值（例如 `com.example.fchord_coach`）。後續 Task 8 的 Kotlin 檔案 `package` 宣告需與此一致。

- [ ] **Step 2：新增 MediaPipe dependency**

在 `frontend/android/app/build.gradle` 的 `dependencies {}` 區塊加入：
```gradle
implementation 'com.google.mediapipe:tasks-vision:0.10.14'
```

- [ ] **Step 3：下載 MediaPipe Hand Landmarker 模型**

```bash
mkdir -p frontend/android/app/src/main/assets
curl -L -o frontend/android/app/src/main/assets/hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

- [ ] **Step 4：確認 Gradle sync 成功**

```bash
cd frontend
flutter pub get
```

在 Android Studio 或：
```bash
cd frontend/android
./gradlew assembleDebug
```

預期：BUILD SUCCESSFUL（下載 MediaPipe dependency）

- [ ] **Step 5：Commit**

```bash
git add frontend/android/app/build.gradle \
        frontend/android/app/src/main/assets/hand_landmarker.task
git commit -m "chore(android): 新增 MediaPipe Tasks Vision 依賴與 hand_landmarker 模型"
```

---

### Task 8：MediaPipeHandsChannel.kt + MainActivity 註冊（BL-003）

**Files:**
- Create: `frontend/android/app/src/main/kotlin/<pkg>/MediaPipeHandsChannel.kt`
- Modify: `frontend/android/app/src/main/kotlin/<pkg>/MainActivity.kt`

> `<pkg>` 替換為 Task 7 Step 1 確認的路徑（例如 `com/example/fchord_coach`）

- [ ] **Step 1：建立 MediaPipeHandsChannel.kt**

`frontend/android/app/src/main/kotlin/<pkg>/MediaPipeHandsChannel.kt`：
```kotlin
package <your.package.name>  // 替換為實際 package name

import android.content.Context
import android.graphics.BitmapFactory
import com.google.mediapipe.framework.image.BitmapImageBuilder
import com.google.mediapipe.tasks.core.BaseOptions
import com.google.mediapipe.tasks.vision.core.RunningMode
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarker
import com.google.mediapipe.tasks.vision.handlandmarker.HandLandmarkerOptions
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MediaPipeHandsChannel(flutterEngine: FlutterEngine, context: Context) {

    companion object {
        const val CHANNEL = "mediapipe_hands/landmarks"
    }

    private val landmarker: HandLandmarker by lazy {
        val options = HandLandmarkerOptions.builder()
            .setBaseOptions(
                BaseOptions.builder()
                    .setModelAssetPath("hand_landmarker.task")
                    .build()
            )
            .setNumHands(1)
            .setRunningMode(RunningMode.IMAGE)
            .build()
        HandLandmarker.createFromOptions(context, options)
    }

    init {
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                if (call.method == "getLandmarks") {
                    val jpegBytes = call.arguments as? ByteArray
                    if (jpegBytes == null) {
                        result.error("INVALID_ARG", "Expected ByteArray", null)
                        return@setMethodCallHandler
                    }
                    handleGetLandmarks(jpegBytes, result)
                } else {
                    result.notImplemented()
                }
            }
    }

    private fun handleGetLandmarks(jpegBytes: ByteArray, result: MethodChannel.Result) {
        try {
            val bitmap = BitmapFactory.decodeByteArray(jpegBytes, 0, jpegBytes.size)
                ?: return result.success(null)
            val mpImage = BitmapImageBuilder(bitmap).build()
            val detection = landmarker.detect(mpImage)
            if (detection.landmarks().isEmpty()) {
                result.success(null)
                return
            }
            val landmarks = detection.landmarks()[0].map { lm ->
                mapOf(
                    "x" to lm.x().toDouble(),
                    "y" to lm.y().toDouble(),
                    "z" to lm.z().toDouble(),
                )
            }
            result.success(landmarks)
        } catch (e: Exception) {
            result.error("MEDIAPIPE_ERROR", e.message, null)
        }
    }
}
```

- [ ] **Step 2：修改 MainActivity.kt 註冊 channel**

找到 `frontend/android/app/src/main/kotlin/<pkg>/MainActivity.kt`，加入：
```kotlin
package <your.package.name>  // 保留原有 package 宣告

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MediaPipeHandsChannel(flutterEngine, applicationContext)
    }
}
```

- [ ] **Step 3：Gradle build 確認編譯通過**

```bash
cd frontend/android
./gradlew assembleDebug
```

預期：`BUILD SUCCESSFUL`

- [ ] **Step 4：Commit**

```bash
git add frontend/android/app/src/main/kotlin/
git commit -m "feat(android): 新增 MediaPipeHandsChannel 與 MainActivity 註冊"
```

---

### Task 9：CameraPage Slice 2（真實相機 + Platform Channel）（BL-003）

**Files:**
- Modify: `frontend/lib/features/camera/camera_page.dart`

- [ ] **Step 1：更新 CameraPage 為 ConsumerStatefulWidget**

`frontend/lib/features/camera/camera_page.dart`：
```dart
import 'dart:async';
import 'dart:typed_data';
import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/infer_provider.dart';
import '../feedback/feedback_page.dart';

class CameraPage extends ConsumerStatefulWidget {
  const CameraPage({super.key});

  @override
  ConsumerState<CameraPage> createState() => _CameraPageState();
}

class _CameraPageState extends ConsumerState<CameraPage> {
  static const _channel = MethodChannel('mediapipe_hands/landmarks');

  CameraController? _controller;
  Timer? _inferTimer;
  bool _isProcessing = false;

  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    final cameras = await availableCameras();
    if (cameras.isEmpty) return;
    final front = cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.front,
      orElse: () => cameras.first,
    );
    _controller = CameraController(
      front,
      ResolutionPreset.medium,
      enableAudio: false,
    );
    await _controller!.initialize();
    if (!mounted) return;
    setState(() {});
    _inferTimer = Timer.periodic(
      const Duration(milliseconds: 800),
      (_) => _analyzeFrame(),
    );
  }

  Future<void> _analyzeFrame() async {
    if (_isProcessing || _controller == null || !_controller!.value.isInitialized) {
      return;
    }
    _isProcessing = true;
    try {
      final file = await _controller!.takePicture();
      final jpegBytes = await file.readAsBytes();
      final raw = await _channel.invokeMethod<List<dynamic>>('getLandmarks', jpegBytes);
      if (raw == null || !mounted) return;
      final landmarks = raw.map((e) {
        final map = Map<String, dynamic>.from(e as Map);
        return map.map((k, v) => MapEntry(k, (v as num).toDouble()));
      }).toList();
      await ref.read(inferProvider.notifier).infer(landmarks);
    } catch (_) {
      // 忽略單幀錯誤，繼續下一幀
    } finally {
      _isProcessing = false;
    }
  }

  @override
  void dispose() {
    _inferTimer?.cancel();
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final inferState = ref.watch(inferProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('F Chord Coach')),
      body: Column(
        children: [
          Expanded(
            child: _controller?.value.isInitialized == true
                ? CameraPreview(_controller!)
                : const Center(child: CircularProgressIndicator()),
          ),
          inferState.when(
            data: (result) => result != null
                ? FeedbackPage(result: result)
                : const SizedBox(height: 8),
            loading: () => const LinearProgressIndicator(),
            error: (e, _) => Padding(
              padding: const EdgeInsets.all(8),
              child: Text('錯誤：$e',
                  style: const TextStyle(color: Colors.red)),
            ),
          ),
        ],
      ),
    );
  }
}
```

- [ ] **Step 2：在 Android 實機執行（需允許相機權限）**

確認 `frontend/android/app/src/main/AndroidManifest.xml` 包含：
```xml
<uses-permission android:name="android.permission.CAMERA" />
```

```bash
cd frontend
flutter run
```

手放入鏡頭，確認 FeedbackPage 會更新。

- [ ] **Step 3：flutter analyze**

```bash
cd frontend
flutter analyze lib/
```

預期：`No issues found!`

- [ ] **Step 4：Commit**

```bash
git add frontend/lib/features/camera/camera_page.dart
git commit -m "feat(frontend): CameraPage Slice 2 — 真實相機 + MediaPipe Platform Channel 偵測"
```

---

## Slice 3 — UI 完整化

### Task 10：HandSkeletonPainter CustomPainter（BL-004）

**Branch:**
```bash
git checkout develop && git pull
git checkout -b feat/BL-004-hand-skeleton
```

**Files:**
- Create: `frontend/lib/features/camera/hand_skeleton_painter.dart`

- [ ] **Step 1：建立 HandSkeletonPainter**

`frontend/lib/features/camera/hand_skeleton_painter.dart`：
```dart
import 'package:flutter/material.dart';

/// MediaPipe Hand Landmarker 21 節點連線拓撲
const _connections = [
  // 拇指
  [0, 1], [1, 2], [2, 3], [3, 4],
  // 食指
  [0, 5], [5, 6], [6, 7], [7, 8],
  // 中指
  [0, 9], [9, 10], [10, 11], [11, 12],
  // 無名指
  [0, 13], [13, 14], [14, 15], [15, 16],
  // 小指
  [0, 17], [17, 18], [18, 19], [19, 20],
  // 掌心
  [5, 9], [9, 13], [13, 17],
];

class HandSkeletonPainter extends CustomPainter {
  final List<Map<String, double>> landmarks;

  HandSkeletonPainter(this.landmarks);

  @override
  void paint(Canvas canvas, Size size) {
    if (landmarks.length != 21) return;

    final linePaint = Paint()
      ..color = Colors.greenAccent
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;

    final dotPaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;

    // 連線
    for (final conn in _connections) {
      final a = landmarks[conn[0]];
      final b = landmarks[conn[1]];
      canvas.drawLine(
        Offset(a['x']! * size.width, a['y']! * size.height),
        Offset(b['x']! * size.width, b['y']! * size.height),
        linePaint,
      );
    }

    // 節點
    for (final lm in landmarks) {
      canvas.drawCircle(
        Offset(lm['x']! * size.width, lm['y']! * size.height),
        4,
        dotPaint,
      );
    }
  }

  @override
  bool shouldRepaint(HandSkeletonPainter old) => old.landmarks != landmarks;
}
```

- [ ] **Step 2：flutter analyze**

```bash
cd frontend
flutter analyze lib/features/camera/hand_skeleton_painter.dart
```

預期：`No issues found!`

- [ ] **Step 3：Commit**

```bash
git add frontend/lib/features/camera/hand_skeleton_painter.dart
git commit -m "feat(frontend): 新增 HandSkeletonPainter CustomPainter（21 節點骨架）"
```

---

### Task 11：CameraPage Slice 3 — 骨架 Overlay 整合（BL-004）

**Files:**
- Modify: `frontend/lib/features/camera/camera_page.dart`

- [ ] **Step 1：在 provider 中保存最新 landmarks**

在 `frontend/lib/providers/infer_provider.dart` 末尾加入 landmarks provider：
```dart
final landmarksProvider = StateProvider<List<Map<String, double>>>((_) => []);
```

在 `InferNotifier.infer()` 的 `AsyncValue.guard` 前加一行儲存 landmarks：
```dart
Future<void> infer(List<Map<String, double>> landmarks) async {
  ref.read(landmarksProvider.notifier).state = landmarks;  // 新增這行
  state = const AsyncValue.loading();
  state = await AsyncValue.guard(() async {
    final json = await ref.read(apiClientProvider).infer(landmarks);
    return InferResult.fromJson(json);
  });
}
```

- [ ] **Step 2：在 CameraPage 加入骨架 overlay**

修改 `frontend/lib/features/camera/camera_page.dart` 的相機預覽區塊，把原本的 `CameraPreview(_controller!)` 包進 `Stack`：

```dart
// 在 import 頂部加入
import 'hand_skeleton_painter.dart';

// 在 build() 中，將相機預覽部分改為：
Expanded(
  child: _controller?.value.isInitialized == true
      ? Stack(
          fit: StackFit.expand,
          children: [
            CameraPreview(_controller!),
            Consumer(
              builder: (context, ref, _) {
                final landmarks = ref.watch(landmarksProvider);
                if (landmarks.isEmpty) return const SizedBox.shrink();
                return CustomPaint(
                  painter: HandSkeletonPainter(landmarks),
                );
              },
            ),
          ],
        )
      : const Center(child: CircularProgressIndicator()),
),
```

- [ ] **Step 3：在實機確認骨架顯示在相機畫面上**

```bash
cd frontend
flutter run
```

手放入鏡頭，確認：
- 相機預覽正常
- 偵測到手時綠色骨架 overlay 顯示於正確位置
- FeedbackPage 顯示 error_type 與建議

- [ ] **Step 4：flutter analyze**

```bash
cd frontend
flutter analyze lib/
```

預期：`No issues found!`

- [ ] **Step 5：Commit**

```bash
git add frontend/lib/providers/infer_provider.dart \
        frontend/lib/features/camera/camera_page.dart
git commit -m "feat(frontend): CameraPage Slice 3 — 手勢骨架 overlay 整合完成"
```

---

## 完成後驗收

對照 spec 中的驗收條件逐項確認：

- [ ] `POST /infer` 接受 21 landmarks，回傳合法 JSON（stub 模式）
- [ ] VLMService 真實 API 呼叫可運作（需設定 `VLM_API_KEY` 在 `backend/.env`）
- [ ] Flutter App 在 Android 實機開啟相機正常
- [ ] MediaPipe 偵測到手部時，landmarks 被送出 `/infer` 請求
- [ ] FeedbackPage 顯示 error_type（繁體中文 label）、confidence bar、suggestion
- [ ] 骨架 overlay 正確繪製在相機畫面上的手部位置
- [ ] `flutter analyze` 與 `python -m pytest tests/ -v` 全數通過

---

## 注意事項

- **ONNX 模型：** `backend/models/fchord_gnn.onnx` 由 HansonChu 交付後放入此路徑，GNNService 會自動從 stub 切換到真實推論，無需其他程式碼修改。
- **VLM API Key：** 在 `backend/.env` 設定 `VLM_API_KEY` 與 `VLM_PROVIDER`，不要 commit `.env` 檔。
- **Android Package Name：** Task 8 的 Kotlin 檔案 `package` 宣告必須與 `build.gradle` 的 `applicationId` 一致。
- **不直接 commit 到 develop/main：** 每個 feature branch 完成後開 PR，等 review 後 merge。
