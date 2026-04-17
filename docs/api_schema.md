# API Schema

## POST /infer

Backend 接收 MediaPipe landmarks，回傳 GNN 分析結果。

### Request

```json
{
  "nodes": [[0.52, 0.33, -0.02], "...21 items"]
}
```

| Field   | Type             | Description                          |
|---------|------------------|--------------------------------------|
| `nodes` | `float[21][3]`   | MediaPipe normalized landmarks 0–1   |

### Response

```json
{
  "nodes":             [[0.52, 0.33, -0.02], "..."],
  "node_status":       [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  "label":             "err_index_low",
  "confidence":        0.87,
  "ghost_nodes":       [[0.50, 0.30], "...21 items"],
  "error_duration_ms": 3200,
  "suggestion":        "食指第一關節角度偏低，試著抬高手腕",
  "frame_ms":          18
}
```

| Field               | Type             | Description                                      |
|---------------------|------------------|--------------------------------------------------|
| `nodes`             | `float[21][3]`   | Echo of input                                    |
| `node_status`       | `int[21]`        | Per-node: 0=ok, 1=warn, 2=error                 |
| `label`             | `string`         | GNN classification result                        |
| `confidence`        | `float`          | Softmax confidence 0–1                           |
| `ghost_nodes`       | `float[21][2]`   | Target F chord skeleton (x, y only)              |
| `error_duration_ms` | `int`            | Consecutive error duration in ms                 |
| `suggestion`        | `string \| null` | VLM suggestion, null if not triggered            |
| `frame_ms`          | `int`            | Inference latency in ms                          |

## ONNX Input Spec (for Backend Team)

```python
x          = np.array(nodes, dtype=np.float32)   # [21, 3]
edge_index = EDGE_INDEX.numpy().astype(np.int64) # [2, 46]  — from src/graph.py
batch      = np.zeros(21, dtype=np.int64)         # all nodes belong to graph 0
```
