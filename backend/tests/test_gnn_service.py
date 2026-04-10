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
