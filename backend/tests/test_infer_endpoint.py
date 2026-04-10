import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _landmarks() -> list[dict[str, float]]:
    return [{"x": 0.5, "y": 0.5, "z": 0.0} for _ in range(21)]


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_infer_stub_response() -> None:
    with patch(
        "app.routers.infer.vlm_service.suggest",
        new_callable=AsyncMock,
        return_value="食指壓平，加油！",
    ):
        resp = client.post("/infer", json={"landmarks": _landmarks()})

    assert resp.status_code == 200
    data = resp.json()
    assert data["error_type"] == "correct"
    assert abs(data["confidence"] - 0.99) < 1e-6
    assert data["suggestion"] == "食指壓平，加油！"


def test_infer_rejects_missing_fields() -> None:
    resp = client.post("/infer", json={"landmarks": [{"x": 0.5} for _ in range(21)]})
    assert resp.status_code == 422
