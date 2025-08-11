# app/main.py
from __future__ import annotations

import json
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import xgboost as xgb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.status import HTTP_400_BAD_REQUEST

# -----------------------------
# Env & logging
# -----------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("penguin-api")

# -----------------------------
# Enums & request model
# -----------------------------
class Island(str, Enum):
    Torgersen = "Torgersen"
    Biscoe = "Biscoe"
    Dream = "Dream"


class Sex(str, Enum):
    male = "male"
    female = "female"


class PenguinFeatures(BaseModel):
    bill_length_mm: float
    bill_depth_mm: float
    flipper_length_mm: float
    body_mass_g: float
    year: int
    sex: Sex
    island: Island


# -----------------------------
# App & globals
# -----------------------------
app = FastAPI()

# In-memory state set at startup
booster: Optional[xgb.Booster] = None
FEATURE_COLUMNS: List[str] = []
LABEL_CLASSES: List[str] = []
SOURCE: str = "unknown"  # "gcs" | "local" | "unknown"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"detail": exc.errors()})


# -----------------------------
# Helpers
# -----------------------------
def _build_label_classes(enc: Dict[str, Any]) -> List[str]:
    """
    Build ordered class list from encoders.json's label_encoder mapping,
    which looks like: {"Adelie":"0","Chinstrap":"1","Gentoo":"2",...}
    """
    le_map: Dict[str, int] = {name: int(idx) for name, idx in enc["label_encoder"].items()}
    classes: List[Optional[str]] = [None] * (max(le_map.values()) + 1)
    for name, idx in le_map.items():
        classes[idx] = name
    # type: ignore[return-value]
    return [c or "" for c in classes]


def _load_local() -> tuple[xgb.Booster, Dict[str, Any]]:
    """Load model & encoders from app/data/."""
    here: Path = Path(__file__).parent
    model_path: Path = here / "data" / "model.json"
    enc_path: Path = here / "data" / "encoders.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Local model file not found: {model_path}")
    if not enc_path.exists():
        raise FileNotFoundError(f"Local encoders file not found: {enc_path}")

    b = xgb.Booster()
    b.load_model(str(model_path))
    with open(enc_path, "r", encoding="utf-8") as f:
        enc = json.load(f)

    logger.info("Loaded model & encoders from LOCAL paths")
    return b, enc


def _load_from_gcs() -> tuple[xgb.Booster, Dict[str, Any]]:
    """
    Download model (and optionally encoders) from GCS via ADC / GOOGLE_APPLICATION_CREDENTIALS.
    Requires:
      - GCS_BUCKET_NAME
      - GCS_MODEL_BLOB or GCS_BLOB_NAME
    Optional:
      - GCS_ENCODER_BLOB (if omitted, will fall back to local encoders)
    """
    bucket_name: Optional[str] = os.getenv("GCS_BUCKET_NAME")
    model_blob: str = os.getenv("GCS_MODEL_BLOB") or os.getenv("GCS_BLOB_NAME") or "model.json"
    enc_blob: Optional[str] = os.getenv("GCS_ENCODER_BLOB")

    if not bucket_name:
        raise RuntimeError("GCS_BUCKET_NAME not set")

    # Lazy import so local dev can run without the SDK installed.
    from google.cloud import storage

    logger.info(
        "Attempting GCS load via ADC: bucket=%s model_blob=%s encoder_blob=%s",
        bucket_name,
        model_blob,
        enc_blob,
    )

    client = storage.Client()  # uses ADC (env var or metadata server)
    bucket = client.bucket(bucket_name)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # model
        model_path = tmp / "model.json"
        bucket.blob(model_blob).download_to_filename(str(model_path))
        b = xgb.Booster()
        b.load_model(str(model_path))
        logger.info("GCS: model downloaded & Booster loaded")

        # encoders
        enc: Dict[str, Any]
        if enc_blob:
            enc_path = tmp / "encoders.json"
            bucket.blob(enc_blob).download_to_filename(str(enc_path))
            with open(enc_path, "r", encoding="utf-8") as f:
                enc = json.load(f)
            logger.info("GCS: encoders downloaded")
        else:
            # local fallback for encoders if not provided in GCS
            here = Path(__file__).parent
            with open(here / "data" / "encoders.json", "r", encoding="utf-8") as f:
                enc = json.load(f)
            logger.info("GCS: used LOCAL encoders (no GCS_ENCODER_BLOB provided)")

    return b, enc


# -----------------------------
# Lifespan: load at startup
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global booster, FEATURE_COLUMNS, LABEL_CLASSES, SOURCE
    app.state.model_ready = False
    try:
        # Try GCS first if env is present
        if os.getenv("GCS_BUCKET_NAME") and (os.getenv("GCS_MODEL_BLOB") or os.getenv("GCS_BLOB_NAME")):
            b, enc = _load_from_gcs()
            SOURCE = "gcs"
        else:
            raise RuntimeError("GCS env not provided; falling back to local")

        FEATURE_COLUMNS = enc["feature_columns"]
        LABEL_CLASSES = _build_label_classes(enc)
        booster = b
        app.state.model_ready = True
        logger.info("Startup complete; model_ready=True; source=GCS")
    except Exception as e:
        logger.warning("GCS load failed (%s). Trying LOCAL...", e, exc_info=True)
        try:
            b, enc = _load_local()
            FEATURE_COLUMNS = enc["feature_columns"]
            LABEL_CLASSES = _build_label_classes(enc)
            booster = b
            SOURCE = "local"
            app.state.model_ready = True
            logger.info("Startup complete; model_ready=True; source=LOCAL")
        except Exception:
            logger.exception("Startup failed (local fallback also failed)")
            app.state.model_ready = False
            SOURCE = "unknown"

    yield
    # no teardown needed


# Recreate app with lifespan enabled
app = FastAPI(lifespan=lifespan)


# -----------------------------
# Routes
# -----------------------------
@app.get("/", include_in_schema=False)
def root() -> Dict[str, str]:
    return {"message": "Hello! Welcome to the Penguins Classification API."}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok" if app.state.model_ready else "degraded", "source": SOURCE}


@app.post("/predict")
def predict(features: PenguinFeatures) -> Dict[str, Any]:
    if not app.state.model_ready or booster is None:
        raise HTTPException(status_code=503, detail="Model not ready")

    try:
        # Convert enums -> strings so get_dummies works consistently
        payload: Dict[str, Any] = features.model_dump()
        payload["sex"] = features.sex.value
        payload["island"] = features.island.value
        logger.info("Prediction requested: %s", payload)

        # Build frame to match training features exactly
        df = pd.DataFrame([payload])
        df = pd.get_dummies(df, columns=["sex", "island"])
        df = df.reindex(columns=FEATURE_COLUMNS, fill_value=0).astype("float32")

        # Predict using Booster; skip feature-name validation (model trained without names)
        dm = xgb.DMatrix(df.values)
        preds = booster.predict(dm, validate_features=False)

        if preds.ndim == 2 and preds.shape[1] > 1:
            pred_idx: int = int(np.argmax(preds[0]))
        else:
            pred_idx = int(np.ravel(preds)[0])

        species: str = LABEL_CLASSES[pred_idx]
        return {"species": species}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Internal prediction error")
