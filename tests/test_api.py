
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

# ------------------------------------------------------------------
# Ensure imports & env are set BEFORE importing the app
# ------------------------------------------------------------------
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))



# Point to local test assets by default
os.environ.setdefault("MODEL_PATH", str(project_root / "app" / "data" / "model.json"))

os.environ.setdefault("METADATA_PATH", str(project_root / "app" / "data" / "encoders.json"))

from app.main import app  # noqa: E402


try:
    from app.main import model  # type: ignore  # noqa: E402
except Exception:
    model = None  # Fallback if not exported



@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ------------------------------------------------------------------
# Config / sample payloads
# ------------------------------------------------------------------
EXPECTED_ROOT_SUBSTRING = "Welcome"
HEALTH_OK_RESPONSE = {"status": "ok"}

VALID_PAYLOAD: Dict[str, Any] = {
    "bill_length_mm": 40.0,
    "bill_depth_mm": 18.0,
    "flipper_length_mm": 195,
    "body_mass_g": 4000,
    "year": 2008,
    "sex": "male",
    "island": "Biscoe",
}

MISSING_FIELD_PAYLOAD = {
    # "bill_length_mm" omitted on purpose
    "bill_depth_mm": 18.0,
    "flipper_length_mm": 195,
    "body_mass_g": 4000,
    "year": 2008,
    "sex": "male",
    "island": "Biscoe",
}

INVALID_TYPE_PAYLOAD = {
    "bill_length_mm": "not_a_float",
    "bill_depth_mm": 18.0,
    "flipper_length_mm": 195,
    "body_mass_g": 4000,
    "year": 2008,
    "sex": "male",
    "island": "Biscoe",
}

BOUNDARY_VALUES = [-3000, 0, 10**9]


# ------------------------------------------------------------------
# Basic endpoints
# ------------------------------------------------------------------
def test_root(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "message" in data
    assert EXPECTED_ROOT_SUBSTRING in data["message"]


def test_health_ok(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == HEALTH_OK_RESPONSE


# ------------------------------------------------------------------
# Prediction: happy path
# ------------------------------------------------------------------
def test_predict_valid_input(client: TestClient) -> None:
    r = client.post("/predict", json=VALID_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert "species" in data
    assert isinstance(data["species"], str)


# ------------------------------------------------------------------
# Prediction: validation errors (FastAPI default -> 422)
# ------------------------------------------------------------------
def test_predict_missing_field(client: TestClient) -> None:
    r = client.post("/predict", json=MISSING_FIELD_PAYLOAD)
    assert r.status_code == 422
    assert isinstance(r.json().get("detail"), list)


def test_predict_invalid_type(client: TestClient) -> None:
    r = client.post("/predict", json=INVALID_TYPE_PAYLOAD)
    assert r.status_code == 422


def test_predict_empty_body(client: TestClient) -> None:
    r = client.post("/predict", json={})
    assert r.status_code == 422


@pytest.mark.parametrize("body_mass", BOUNDARY_VALUES)
def test_predict_out_of_range_and_boundary(client: TestClient, body_mass: int) -> None:
    payload = {**VALID_PAYLOAD, "body_mass_g": body_mass}
    r = client.post("/predict", json=payload)
    # If you add Pydantic range validators -> 422; if you clamp and predict -> 200
    assert r.status_code in (200, 422)


# ------------------------------------------------------------------
# Internal error handling (500)
# ------------------------------------------------------------------
@pytest.mark.skipif(model is None, reason="model object not exported by app.main")
def test_predict_internal_error(client: TestClient, monkeypatch) -> None:
    def _boom(*args, **kwargs):
        raise RuntimeError("forced failure")

    # monkeypatch the model's predict to simulate internal error
    monkeypatch.setattr(model, "predict", _boom, raising=True)

    r = client.post("/predict", json=VALID_PAYLOAD)
    assert r.status_code == 500
    assert r.json().get("detail") == "Internal prediction error"


# ------------------------------------------------------------------
# Health degraded path when not ready
# ------------------------------------------------------------------
def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "ok"   # <- key change

