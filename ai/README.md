# AI / ML

MediaPipe → GraphSAGE GNN → ONNX pipeline。

## 環境建置

```bash
cd ai
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 資料

訓練資料不進 git。錄製方式見 `tools/label.py`。

## 目錄結構

- `src/`     — 核心程式碼
- `tools/`   — labeling、QC 工具
- `data/`    — 訓練資料（本地，不 push）
- `models/`  — 訓練好的 weights（本地，不 push）
