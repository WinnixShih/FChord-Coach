# FChord Coach — Frontend & Backend MVP Design

Date: 2026-04-09
Author: WinnixShih
Scope: `frontend/`, `backend/` only — `ai/` 由 HansonChu 負責，不在此範圍內

---

## 決策摘要

| 項目 | 決策 |
|------|------|
| 目標平台 | Android only（MVP） |
| MediaPipe 整合方式 | Platform Channel（Kotlin + Android MediaPipe SDK） |
| GNNService MVP 策略 | stub fallback（ONNX 不存在時回傳 `correct` + `0.99`），等 HansonChu 交付後換 |
| VLM Provider | Anthropic（`claude-sonnet-4-6`）或 OpenAI（`gpt-4o`），由 `.env` 切換 |
| 開發策略 | 垂直切片：每切片前後端一起完成 |

---

## 開發切片

### 切片 1 — Pipeline 跑通

目標：整條 request → response 流程可運作，不依賴真實 MediaPipe 或 ONNX。

**Backend：**
- `main.py`：加 `lifespan` context manager，startup 時呼叫 `GNNService.load()`
- `GNNService`：startup 載入 ONNX；model 檔不存在時 stub 回傳 `("correct", 0.99)`
- `VLMService`：實作 `_call_vlm()`，根據 `VLM_PROVIDER` 呼叫 Anthropic 或 OpenAI API

**Frontend：**
- `main.dart`：路由改到 `CameraPage`
- `infer_provider.dart`：`AsyncNotifier`，持有推論結果狀態
- `CameraPage`：暫時用固定假 landmarks（切片 1 測試用），呼叫 `infer_provider`
- `FeedbackPage`：顯示 `error_type` 和 `suggestion` 純文字

### 切片 2 — MediaPipe 接入

目標：用真實手勢驅動推論。

**Frontend（Android）：**
- `MediaPipeHandsChannel.kt`：初始化 `HandLandmarker`，每幀處理後透過 `MethodChannel("mediapipe_hands/landmarks")` 回傳 21 個 `{x, y, z}`
- `CameraPage`：改為從 `camera` package 取得每幀 → 送入 Platform Channel → 更新 `infer_provider`

**Android dependencies（`build.gradle`）：**
```
implementation 'com.google.mediapipe:tasks-vision:0.10.14'
```
（版本以實作時 Maven Central 最新穩定版為準，0.10.14 為 2024 Q4 穩定版）

### 切片 3 — UI 完整化

目標：App 視覺完整，接近正式 MVP。

**Frontend：**
- `hand_skeleton_painter.dart`：`CustomPainter`，依 MediaPipe Hand 拓撲連線 21 個 landmarks，overlay 在相機預覽上
- `FeedbackPage`：補上 `LinearProgressIndicator` 顯示 confidence、改善整體排版

**Backend：**
- `GNNService`：ONNX 模型由 HansonChu 交付後，放至 `backend/models/fchord_gnn.onnx`，stub 自動失效（有檔案就載入真實 session）

---

## Backend 詳細設計

### 檔案異動

| 檔案 | 異動 |
|------|------|
| `backend/main.py` | 加 `lifespan`，startup 呼叫 `GNNService.load()` |
| `backend/app/services/gnn_service.py` | 重寫為 startup 載入 + stub fallback |
| `backend/app/services/vlm_service.py` | 實作 `_call_vlm()`（Anthropic / OpenAI） |
| `backend/requirements.txt` | 新增 `anthropic`、`openai` |
| `backend/app/routers/infer.py` | 不動 |

### GNNService 行為

```python
# startup 時呼叫一次
def load(self) -> None:
    if os.path.exists(self._model_path):
        self._session = ort.InferenceSession(self._model_path)
    # 否則維持 None → stub mode

def classify(self, landmarks) -> tuple[str, float]:
    if self._session is None:
        return "correct", 0.99  # stub
    # 真實 ONNX 推論
```

### VLMService Prompt

```
System: 你是一位吉他老師，專門幫學生矯正 F 和弦指型。
User: 學生的手型有問題：{error_type}。給一句簡短（30字以內）、鼓勵的建議。
```

兩個 provider 使用相同 prompt，差異只在 SDK 呼叫方式：
- `anthropic`：`anthropic.Anthropic().messages.create(model="claude-sonnet-4-6", ...)`
- `openai`：`openai.AsyncOpenAI().chat.completions.create(model="gpt-4o", ...)`

Rate limit：2 calls/min，超限時回傳預設語句（現有邏輯不動）。

---

## Frontend 詳細設計

### 檔案異動

| 檔案 | 異動 |
|------|------|
| `frontend/lib/main.dart` | 路由到 `CameraPage` |
| `frontend/lib/features/camera/camera_page.dart` | 相機預覽 + MediaPipe 觸發（切片 1 用假資料） |
| `frontend/lib/features/camera/hand_skeleton_painter.dart` | 新增，CustomPainter（切片 3） |
| `frontend/lib/features/feedback/feedback_page.dart` | 完整 UI（error_type、suggestion、confidence bar） |
| `frontend/lib/providers/infer_provider.dart` | 新增，AsyncNotifier |
| `android/app/src/main/kotlin/.../MediaPipeHandsChannel.kt` | 新增，Platform Channel（切片 2） |
| `frontend/pubspec.yaml` | 不動（套件已足夠） |

### 狀態管理

```
InferNotifier (AsyncNotifier<InferResult?>)
  - state: AsyncValue<InferResult?>
  - infer(List<Landmark> landmarks): 呼叫 ApiClient，更新 state

InferResult {
  errorType: String
  confidence: double
  suggestion: String
}
```

### Platform Channel 介面

```dart
// Flutter 側
static const _channel = MethodChannel('mediapipe_hands/landmarks');
// 傳入 Uint8List（JPEG 格式，由 camera package 的 CameraImage 轉換）
final raw = await _channel.invokeMethod<List>('getLandmarks', jpegBytes);
// 回傳 List<Map<String, double>> 共 21 個 {x, y, z}
```

`CameraImage`（YUV_420_888）先在 Flutter 側轉成 JPEG `Uint8List` 再傳入 channel，Kotlin 側用 `BitmapFactory.decodeByteArray` 解碼後送入 MediaPipe。

### 骨架連線拓撲（CustomPainter）

MediaPipe Hand 21 個節點依官方拓撲連線：
- 手腕 → 拇指（0→1→2→3→4）
- 手腕 → 食指（0→5→6→7→8）
- 手腕 → 中指（0→9→10→11→12）
- 手腕 → 無名指（0→13→14→15→16）
- 手腕 → 小指（0→17→18→19→20）
- 掌心連線（5→9→13→17）

---

## 範圍外（MVP 不包含）

- `ai/` 目錄（HansonChu 負責）
- BL-008 本地練習歷史（sqflite）
- BL-007 CI Pipeline
- iOS 支援
- 多和弦支援
- 設定頁、Onboarding

---

## 驗收條件（MVP 完成定義）

- [ ] `POST /infer` 接受 21 landmarks，回傳合法 JSON（stub 或真實 ONNX）
- [ ] VLM 真實呼叫可運作（需 API key 設定）
- [ ] Flutter App 可在 Android 上開啟相機
- [ ] MediaPipe 從相機幀取得 21 landmarks 並送出 API request
- [ ] FeedbackPage 顯示 error_type、confidence、suggestion
- [ ] 手勢骨架 overlay 正確繪製在相機畫面上
