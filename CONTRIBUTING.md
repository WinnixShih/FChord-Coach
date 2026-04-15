# Contributing to FChord Coach

Two-person project. Keep the workflow tight and the history clean.

## Ownership

| 負責人 | 範圍 |
|--------|------|
| **WinnixShih** | `frontend/`、`backend/` |
| **HansonChu** | `ai/`（GNN 訓練、ONNX export、資料處理） |

不得越線改對方的目錄，除非先對齊過。

## Branching

**禁止直接 commit 或 push 到 `main`、`master`、`develop`。**

所有開發在 feature branch 進行：

```bash
git checkout develop && git pull
git checkout -b feat/BL-{ID}-{slug}        # 新功能
# 或
git checkout -b fix/{slug}                  # 修復
# 或
git checkout -b docs/{slug}                 # 純文件
```

### 命名格式

- 新功能：`feat/BL-005-flutter-camera`
- 修復：`fix/infer-endpoint-crash`
- 文件：`docs/update-api-schema`

## Commit messages

格式：`<類型>(<scope>): <描述（繁體中文）>`

- 類型：`feat`、`fix`、`refactor`、`test`、`docs`、`chore`
- scope 通常是 `frontend` / `backend` / `ai` / `docs`
- 範例：
  - `feat(backend): 新增 /infer endpoint 並整合 GNN 推論`
  - `fix(frontend): 修正 camera permission 未授權時 crash`
  - `docs: 更新 README 啟動流程`

### Commit 粒度

每個 commit 對應一個邏輯單元。不要 mega-commit，也不要把一個功能拆成十個無意義的 commit。

## Pull Requests

1. 開 PR 目標為 `main`（`develop` 走 `/merge-to-develop` skill，不開 PR — 見 MEMORY）。
2. PR 標題沿用 commit message 格式。
3. PR 描述包含：
   - 這個 PR 解決什麼問題（**為什麼**比**做了什麼**更重要）
   - 測試方式（指令 / 手動驗證步驟）
   - 相關 ticket / backlog 編號
4. 等 review 後再 merge，不要 self-merge 除非對方明確同意。

## CI 要求

GitHub Actions 會在每個 push / PR 上跑：

- `pytest`（backend）
- `flutter analyze`（frontend）

兩個都必須綠。本地先跑過再 push：

```bash
cd backend && pytest
cd frontend && flutter analyze
```

## Coding standards

- **Python**：型別標注完整，不使用裸 `Any`；Pydantic v2 做 I/O 驗證。
- **Dart**：遵循 Flutter 官方 style guide，widget 保持單一職責。
- 不加多餘的 docstring / comment（除非邏輯不顯然）。
- 不留 TODO、hardcode 測試資料、或 debug print。
- UI 相關改動先讀 `DESIGN.md`。

## 文件維護

- 技術棧、目錄結構、API 契約、分支規範有任何變更，同步更新 `CLAUDE.md` 與對應 `docs/`。
- 同一類錯誤發生超過三次，把原因與正確做法記進 `CLAUDE.md` 對應段落。
