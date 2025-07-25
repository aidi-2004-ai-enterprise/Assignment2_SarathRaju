from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
import xgboost as xgb
import numpy as np
import pandas as pd
import json
import logging
import os
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
#Enum class for validating known values for sex and island
class Island(str, Enum):
    
    Torgersen = "Torgersen"
    Biscoe = "Biscoe"
    Dream = "Dream"

class Sex(str, Enum):

    #Enum for valid penguin sex options.

    male = "male"
    female = "female"

class PenguinFeatures(BaseModel):
    
    #Fields user need to provide for prediction
    
    bill_length_mm: float
    bill_depth_mm: float
    flipper_length_mm: float
    body_mass_g: float
    year: int
    sex: Sex
    island: Island

app = FastAPI()
#Filepath
MODEL_PATH: str = os.path.join(os.path.dirname(__file__), "data", "model.json")
ENCODER_PATH: str = os.path.join(os.path.dirname(__file__), "data", "encoders.json")

@app.on_event("startup")
def load_model_and_encoders() -> None:
    
    #Load the XGBoost model and encoder metadata at startup.

    global model, encoders, label_decoder
    model = xgb.XGBClassifier()
    model.load_model(MODEL_PATH)
    logging.info("Loaded model from %s", MODEL_PATH)

    #Opens encoders.json and loads its contents into the encoders dictionary, so the API uses the exact same encoding rules at prediction time as during training.
    with open(ENCODER_PATH, "r") as f:
        encoders = json.load(f)

    """ This creates a dictionary (label_decoder) that maps the 
    predicted numeric label (e.g., 0) back to the original species name (e.g., "Adelie") for readable API responses."""
    
    label_decoder = {int(v): k for k, v in encoders["label_encoder"].items()}

    from typing import Dict

@app.get("/", include_in_schema=False)
def root() -> Dict[str, str]:
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to the Penguin Classification API! Visit /docs for usage."}
    

@app.post("/predict")
def predict(features: PenguinFeatures) -> Dict[str, Any]:
    """
    Predict the penguin species from validated input features.
    Returns a dictionary with the predicted species name.
    """
    try:
        # Prepare DataFrame from input
        X_input = pd.DataFrame([{
            "bill_length_mm": features.bill_length_mm,
            "bill_depth_mm": features.bill_depth_mm,
            "flipper_length_mm": features.flipper_length_mm,
            "body_mass_g": features.body_mass_g,
            "year": features.year,
        }])
        # One-hot encode categorical variables
        for sex_col in encoders["sex_categories"]:
            X_input[sex_col] = 1 if sex_col == f"sex_{features.sex}" else 0
        for island_col in encoders["island_categories"]:
            X_input[island_col] = 1 if island_col == f"island_{features.island}" else 0
        # Ensure all columns match the training set
        X_input = X_input.reindex(encoders["feature_columns"], axis=1, fill_value=0)
        # Predict species
        pred_idx = int(model.predict(X_input)[0])
        pred_label = label_decoder[pred_idx]
        logging.info("Prediction successful for input: %s, predicted: %s", features.dict(), pred_label)
        return {"species": pred_label}
    except Exception as e:
        logging.error("Prediction failed: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(e)}")
    
    


