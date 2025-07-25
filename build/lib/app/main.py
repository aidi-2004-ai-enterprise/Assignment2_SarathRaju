"""
app/main.py
FastAPI app for penguin species prediction.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
import xgboost as xgb
import numpy as np
import pandas as pd
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Enums for input validation
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

app = FastAPI()

MODEL_PATH = os.path.join(os.path.dirname(__file__), "data", "model.json")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "data", "encoders.json")

@app.on_event("startup")
def load_model_and_encoders():
    global model, encoders, label_decoder
    # Load XGBoost model
    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)
    logging.info("Loaded model from %s", MODEL_PATH)
    # Load encoder info
    with open(ENCODER_PATH, "r") as f:
        encoders = json.load(f)
    # Create label decoder for output
    label_decoder = {v: k for k, v in encoders["label_encoder"].items()}

@app.post("/predict")
def predict(features: PenguinFeatures):
    # Validate: sex and island are already validated by Enum
    try:
        X_input = pd.DataFrame([{
            "bill_length_mm": features.bill_length_mm,
            "bill_depth_mm": features.bill_depth_mm,
            "flipper_length_mm": features.flipper_length_mm,
            "body_mass_g": features.body_mass_g,
            "year": features.year,
        }])
        # One-hot encoding
        for sex_col in encoders["sex_categories"]:
            X_input[sex_col] = 1 if sex_col == f"sex_{features.sex}" else 0
        for island_col in encoders["island_categories"]:
            X_input[island_col] = 1 if island_col == f"island_{features.island}" else 0
        # Reorder columns as during training
        X_input = X_input.reindex(encoders["feature_columns"], axis=1, fill_value=0)
        # Predict
        pred_idx = int(model.predict(X_input)[0])
        pred_label = label_decoder[pred_idx]
        logging.info("Prediction successful for input: %s, predicted: %s", features.dict(), pred_label)
        return {"species": pred_label}
    except Exception as e:
        logging.debug("Prediction failed: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")
