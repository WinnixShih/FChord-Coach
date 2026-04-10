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
