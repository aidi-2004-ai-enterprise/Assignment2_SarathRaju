"""
Trains an XGBoost classifier on the Seaborn penguins dataset, applies one-hot
encoding to categorical features, label-encodes the target, evaluates the model,
and saves both the model and encoders for inference.
"""

from typing import Tuple, Dict, Any
import pandas as pd
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score, accuracy_score
import xgboost as xgb
import json
import os

def load_and_preprocess() -> Tuple[pd.DataFrame, pd.Series, Dict[str, Any]]:
    #Defines a function to load, clean, and encode the data for modeling, 
    # returning the processed features (X), encoded labels (y), and a dictionary of encoder metadata (encoders) needed for consistent prediction.
   
    # Loads the  Penguins dataset and removes rows with missing values 
    df = sns.load_dataset("penguins").dropna()

    #Splits the data into features (X, everything except the species) and target labels (y, which is the species).
    X = df.drop("species", axis=1)
    y = df["species"]

    # Converts categorical columns (sex and island) into one-hot encoded columns, merges them with numeric features, and records the final column order to ensure prediction-time consistency.
    sex_dummies = pd.get_dummies(X["sex"], prefix="sex")
    island_dummies = pd.get_dummies(X["island"], prefix="island")
    X_num = X.drop(["sex", "island"], axis=1)
    X_proc = pd.concat([X_num, sex_dummies, island_dummies], axis=1)
    feature_columns = [str(col) for col in X_proc.columns.tolist()]

    # Turns species names (like “Adelie”) into integer labels (like 0, 1, 2) for model training.
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    """"
    Builds an encoders dictionary containing mappings for label encoding, one-hot columns for sex and island, and the feature column order, all needed for consistent model inference.
    """
    encoders = {
        "label_encoder": {str(k): int(v) for k, v in zip(le.classes_, le.transform(le.classes_))},
        "sex_categories": [str(col) for col in sex_dummies.columns.tolist()],
        "island_categories": [str(col) for col in island_dummies.columns.tolist()],
        "feature_columns": feature_columns
    }
    return X_proc, y_enc, encoders

def main() -> None:
    """Main function to train, evaluate, and save the model and encoders."""
    X, y, encoders = load_and_preprocess()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    model = xgb.XGBClassifier(
        max_depth=3,
        n_estimators=100,
        eval_metric="mlogloss",
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluation
    for split, X_, y_ in [("Train", X_train, y_train), ("Test", X_test, y_test)]:
        pred = model.predict(X_)
        acc = accuracy_score(y_, pred)
        f1 = f1_score(y_, pred, average='weighted')
        print(f"{split} Accuracy: {acc:.3f}, F1: {f1:.3f}")

    # Save model
    os.makedirs("app/data", exist_ok=True)
    model.save_model("app/data/model.json")

    # Save encoders
    with open("app/data/encoders.json", "w") as f:
        json.dump(encoders, f, indent=2)

if __name__ == "__main__":
    main()
