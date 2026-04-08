import numpy as np
import onnxruntime as ort


class GNNService:
    def __init__(self, model_path: str = "models/fchord_gnn.onnx"):
        # session is loaded lazily on first call
        self._session = None
        self._model_path = model_path

    def _get_session(self) -> ort.InferenceSession:
        if self._session is None:
            self._session = ort.InferenceSession(self._model_path)
        return self._session

    def classify(self, landmarks) -> tuple[str, float]:
        coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
        session = self._get_session()
        outputs = session.run(None, {"landmarks": coords[np.newaxis, ...]})
        error_type = outputs[0][0]
        confidence = float(outputs[1][0])
        return error_type, confidence
