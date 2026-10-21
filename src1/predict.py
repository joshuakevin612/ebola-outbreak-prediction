from pathlib import Path

import joblib
import pandas as pd


MODEL_PATH = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "ebola_model.pkl"
)


def load_model():
    return joblib.load(MODEL_PATH)


def predict_risk(model, patient):
    row = pd.DataFrame([patient])

    # Make sure columns are in the exact order used during training
    row = row[model.feature_names_in_]

    probability = model.predict_proba(row)[0][1]

    return probability