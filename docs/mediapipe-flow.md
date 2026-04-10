# MediaPipe Hands 整合流程說明

> 適用：BL-003 Slice 2 — Flutter 相機 + 真實 MediaPipe 手勢偵測

---

## 為什麼需要這個架構？

Flutter 是跨平台框架，**無法直接呼叫 Android SDK**。  
MediaPipe Tasks Vision 是 Google 出的 Android Kotlin library，Flutter 不認識它。

因此需要架一條「橋」讓兩邊溝通，這條橋叫做 **MethodChannel**。

---

## 整體資料流

```
┌─────────────────────────────────────────┐
│              使用者的手機                 │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │        Flutter 層 (Dart)          │   │
│  │                                  │   │
│  │  CameraController                │   │
│  │  （顯示鏡頭畫面）                 │   │
│  │       ↓ 每 2 秒拍一張            │   │
│  │  takePicture() → 暫存 JPEG        │   │
│  │       ↓ 傳 file path              │   │
│  │  MediaPipeChannel.detect(path)   │   │
│  │       ↓ MethodChannel 呼叫        │   │
│  └──────────────────────────────────┘   │
│              ↕  fchord/mediapipe        │
│  ┌──────────────────────────────────┐   │
│  │       Android 層 (Kotlin)         │   │
│  │                                  │   │
│  │  MediaPipeHandsChannel           │   │
│  │  （接收 file path）               │   │
│  │       ↓                          │   │
│  │  HandLandmarker.detect(bitmap)   │   │
│  │       ↓ 21 個關節 {x, y, z}      │   │
│  │  回傳 List<Map> 給 Flutter        │   │
│  └──────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
         ↓ landmarks（21 個座標點）
┌─────────────────────────────────────────┐
│         後端 FastAPI 伺服器              │
│                                         │
│  POST /infer                            │
│  { landmarks: [{x, y, z} × 21] }       │
│       ↓                                 │
│  GNNService → 辨識錯誤類型              │
│  VLMService → 生成自然語言建議           │
│       ↓                                 │
│  { error_type, confidence, suggestion } │
└─────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────┐
│  Flutter FeedbackPage（Bottom Sheet）   │
│  顯示錯誤類型 + 信心指數 + AI 建議文字  │
└─────────────────────────────────────────┘
```

---

## 什麼是 MethodChannel？

MethodChannel 是 Flutter 提供的跨層通訊機制。概念上像一個有名字的對講機：

```
Flutter 端：                      Kotlin 端：
const channel =                  channel.setMethodCallHandler { call ->
  MethodChannel('fchord/mediapipe')   when (call.method) {
                                        "detect" -> { ... }
channel.invokeMethod('detect',        }
  {'path': '/tmp/frame.jpg'})     }
```

兩端用同一個字串名稱（`fchord/mediapipe`）配對。  
Flutter 呼叫 → Kotlin 執行 → 結果回傳給 Flutter。

---

## MediaPipe HandLandmarker 輸出格式

MediaPipe 偵測到手之後，輸出 **21 個關節點**（NormalizedLandmark）：

```
關節編號 → 身體部位
0        → 手腕 (WRIST)
1-4      → 大拇指（CMC → 指尖）
5-8      → 食指（MCP → 指尖）
9-12     → 中指（MCP → 指尖）
13-16    → 無名指（MCP → 指尖）
17-20    → 小指（MCP → 指尖）
```

每個點的座標已正規化到 0.0 ~ 1.0（相對於畫面寬高）：

```json
{"x": 0.43, "y": 0.71, "z": -0.05}
```

- `x`：水平位置（0 = 最左，1 = 最右）
- `y`：垂直位置（0 = 最上，1 = 最下）
- `z`：深度（負值表示比手腕近）

---

## 涉及的檔案

| 層 | 路徑 | 職責 |
|----|------|------|
| Flutter | `lib/services/mediapipe_channel.dart` | MethodChannel Dart 封裝 |
| Flutter | `lib/features/camera/camera_page.dart` | 相機 UI + 定時分析邏輯 |
| Android | `android/app/src/main/kotlin/<pkg>/MediaPipeHandsChannel.kt` | Kotlin channel handler + MediaPipe 推論 |
| Android | `android/app/src/main/kotlin/<pkg>/MainActivity.kt` | 註冊 channel（需手動加 2 行） |
| Android | `android/app/build.gradle` | 加 MediaPipe dependency |
| Assets | `android/app/src/main/assets/hand_landmarker.task` | MediaPipe 手部模型（需手動下載） |

---

## Setup 步驟（首次設定）

### Step 1：flutter create 建立 Android 原生結構

```bash
cd frontend
flutter create . --org com.fchordcoach
```

這會生成 `android/`、`ios/` 等原生平台資料夾。

### Step 2：下載 MediaPipe 模型

```bash
cd frontend/android/app/src/main/assets
curl -O https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

### Step 3：`android/app/build.gradle` 加 dependency

在 `dependencies {}` 區塊內加入：

```gradle
implementation 'com.google.mediapipe:tasks-vision:0.10.14'
```

同時確認 `minSdk` ≥ 24：

```gradle
android {
    defaultConfig {
        minSdk 24
    }
}
```

### Step 4：`MainActivity.kt` 註冊 channel

```kotlin
import com.fchordcoach.app.MediaPipeHandsChannel  // 加這行

class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MediaPipeHandsChannel.register(flutterEngine, this)  // 加這行
    }
}
```

---

## 常見問題

**Q：為什麼不讓 Flutter 直接跑 MediaPipe？**  
A：MediaPipe 的 Flutter plugin（`google_mlkit_pose_detection` 等）存在，但 HandLandmarker 的 Flutter 封裝穩定性較差且版本落後。直接用 Android SDK 最穩定。

**Q：為什麼每 2 秒才分析一次？**  
A：VLM 有 rate limit（2 calls/min）；GNN 推論 < 50ms 目標不要求 60fps。2 秒是合理的教學反饋節奏。

**Q：拍照的 JPEG 暫存在哪？**  
A：`getTemporaryDirectory()` 回傳的 App 暫存目錄，分析完後會被下一張覆蓋。不會積累儲存空間。

**Q：BL-004 骨架 overlay 的 landmarks 從哪來？**  
A：`CameraPage` 在拿到 landmarks 後儲存到 `ValueNotifier<List<Map>>?`，`HandSkeletonPainter`（CustomPainter）讀取這份資料畫在 `CameraPreview` 上方的 Stack 裡。
