# API Schema

## POST /infer

Accepts 21 hand landmarks from MediaPipe and returns chord posture analysis.

### Request

```json
{
  "landmarks": [
    { "x": 0.5, "y": 0.3, "z": 0.01 },
    ...
  ]
}
```

- `landmarks`: Array of exactly 21 objects, each with `x`, `y`, `z` (normalized 0–1)

### Response

```json
{
  "error_type": "index_not_barring",
  "confidence": 0.91,
  "suggestion": "Press your index finger flat across all strings at the 1st fret."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `error_type` | string | Classified posture error (see below) |
| `confidence` | float | Model confidence 0–1 |
| `suggestion` | string | AI-generated improvement tip |

### Error Types

| Value | Description |
|-------|-------------|
| `correct` | F chord posture is correct |
| `index_not_barring` | Index finger not flat across strings |
| `thumb_position` | Thumb too high or low on neck |
| `ring_pinky_curl` | Ring/pinky fingers not curled enough |
| `wrist_angle` | Wrist angle causing string muting |

## GET /health

Returns `{ "status": "ok" }` when the server is running.
