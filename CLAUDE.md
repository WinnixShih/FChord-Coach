# CLAUDE.md — FChord Coach 專案指引

## 專案概覽

**FChord Coach** — 吉他 F 和弦教學 App，使用即時手勢分析 + AI 文字建議幫助使用者矯正指型。

- 使用者對著鏡頭擺 F 和弦，App 即時分析手部姿勢，辨識錯誤類別，並給出 AI 文字建議
- 兩人協作專案（詳見下方「開發邊界」）

## 技術棧

| 層級 | 技術 |
|------|------|
| **Frontend** | Flutter（Dart）、Riverpod、camera、dio、sqflite、MediaPipe Hands |
| **Backend** | Python 3.11+、FastAPI、ONNX Runtime、Pydantic v2、slowapi |
| **AI/ML** | PyTorch Geometric（GraphSAGE GNN）、MediaPipe Hands、ONNX export |
| **VLM** | Claude API（`claude-sonnet-4-6`）或 GPT-4o，rate limit 2 calls/min |

## 專案結構

```
fchord-coach/
├── frontend/              # Flutter mobile app
│   └── lib/
│       ├── features/      # 功能模組（camera、history 等）
│       ├── shared/        # 共用 widget、theme
│       ├── providers/     # Riverpod providers
│       └── services/      # API 呼叫（dio）
├── backend/               # FastAPI inference server
│   └── app/
│       ├── routers/       # 路由層（endpoint 定義）
│       └── services/      # 業務邏輯（GNNService、VLMService）
├── ai/                    # ML 訓練、ONNX export
└── docs/
    ├── api_schema.md      # API request/response 契約
    └── architecture.md    # 系統架構細節
```

## 架構慣例

**後端（FastAPI）：**
- 路由放 `backend/app/routers/`，業務邏輯放 `backend/app/services/`
- Pydantic model 做所有 request/response 驗證
- I/O 密集（VLM 呼叫）用 `async def`，CPU 密集（ONNX 推論）用 `def`
- ONNX 模型在 startup 時載入一次，不要每次推論都重新載入

**前端（Flutter）：**
- 狀態管理統一用 Riverpod（`AsyncNotifier` 處理非同步）
- API 呼叫放 `services/`，UI 放 `features/`，共用元件放 `shared/`
- HTTP 用 `dio`，本地儲存用 `sqflite`

**AI/ML：**
- MediaPipe Hands 輸出 21 個關節點（`x`, `y`, `z` 正規化 0-1）
- GNN error classes：`correct`、`index_not_barring`、`thumb_position`、`ring_pinky_curl`、`wrist_angle`
- 訓練後 export 到 ONNX，放置於 `backend/models/`
- 推論延遲目標：< 50ms（GNN），VLM rate limit 2 calls/min

## Git 分支規範（重要）

**禁止直接 commit 或 push 到 `main`、`master`、`develop`。**

所有開發必須在 feature branch 進行：

```bash
git checkout develop && git pull
git checkout -b feat/BL-{ID}-{slug}   # 新功能
# 或
git checkout -b fix/{slug}             # 修復
```

完成後開 PR，等 review 後 merge。

**分支命名格式：**
- 新功能：`feat/BL-005-flutter-camera`
- 修復：`fix/infer-endpoint-crash`

**Commit message 格式：**`<類型>(<scope>): <描述（繁體中文）>`
- 類型：`feat`、`fix`、`refactor`、`test`、`docs`、`chore`
- 範例：`feat(backend): 新增 /infer endpoint 並整合 GNN 推論`

## 開發邊界

**職責分離，不得越線：**

| 負責人 | 範圍 |
|--------|------|
| **WinnixShih** | `frontend/`、`backend/` |
| **HansonChu** | `ai/`（GNN 訓練、ONNX export、資料處理） |


## 開發規範

- 不加多餘的 docstring、comment（除非邏輯不顯然）
- Python：型別標注完整，不使用裸 `Any`
- Dart：遵循 Flutter 官方 style guide，widget 保持單一職責
- 不留 TODO、hardcode 測試資料、或 debug print
- 每個 commit 對應一個邏輯單元，不要 mega-commit

## CLAUDE.md 維護規則

- **重複出錯：** 若同一類錯誤發生超過三次，將錯誤原因與正確做法記錄到本文件的對應段落，避免再次踩坑
- **架構異動：** 技術棧、目錄結構、API 契約、分支規範有任何重要變更，同步更新本文件，保持與實際狀態一致

## Design System

**所有前端 UI 決策必須先讀 `DESIGN.md`。**

- 美學：Clinical Calm（暖奶油底色、深森林綠 accent、琥珀橙 error）
- 字型：Plus Jakarta Sans（UI）+ Geist Mono（數字）
- CameraPage 使用 Bottom Sheet 回饋，不跳頁
- 手部骨架 overlay：`#52B788` 細線 + `#E07A2F` 錯誤關節圈
- 任何顏色、間距、字型大小偏離 DESIGN.md 者，需明確理由

## 參考文件

- `docs/architecture.md` — 系統架構與資料流
- `docs/api_schema.md` — API request/response 契約
- `docs/mediapipe-flow.md` — MediaPipe MethodChannel 整合流程
- `DESIGN.md` — UI/UX 設計系統（色彩、字型、間距、Layout 規範）
