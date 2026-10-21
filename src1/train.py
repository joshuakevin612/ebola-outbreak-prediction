from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from preprocessing import (
    load_data,
    split_xy,
    build_preprocessor
)


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "ebola_10000_balanced.csv"
MODEL_PATH = BASE_DIR / "models" / "ebola_model.pkl"


def main():
    print("Loading dataset...")

    df = load_data(DATA_PATH)

    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")

    X, y = split_xy(df)

    print(f"Features: {X.shape[1]}")

    print("Target distribution:")
    print(y.value_counts())

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    print()
    print(f"Training samples: {len(X_train)}")
    print(f"Testing samples:  {len(X_test)}")

    pipeline = Pipeline([
        (
            "preprocess",
            build_preprocessor()
        ),
        (
            "model",
            RandomForestClassifier(
                n_estimators=200,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1
            )
        )
    ])

    print()
    print("Training Random Forest...")

    pipeline.fit(X_train, y_train)

    print("Training complete!")

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    print()
    print("=" * 50)
    print("MODEL PERFORMANCE")
    print("=" * 50)

    print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall   : {recall_score(y_test, y_pred):.4f}")
    print(f"F1-score : {f1_score(y_test, y_pred):.4f}")
    print(f"ROC-AUC  : {roc_auc_score(y_test, y_proba):.4f}")

    print()
    print("Confusion Matrix")
    print("(Rows = Actual, Columns = Predicted)")
    print()

    print(confusion_matrix(y_test, y_pred))

    print()
    print("Classification Report")
    print()

    print(
        classification_report(
            y_test,
            y_pred,
            target_names=["Negative", "Positive"]
        )
    )

    names = pipeline.named_steps[
        "preprocess"
    ].get_feature_names_out()

    importances = pd.Series(
        pipeline.named_steps[
            "model"
        ].feature_importances_,
        index=names
    ).sort_values(ascending=False)

    print()
    print("=" * 50)
    print("TOP 15 FEATURES")
    print("=" * 50)

    print(importances.head(15))

    # Create the models folder if it doesn't already exist
    MODEL_PATH.parent.mkdir(exist_ok=True)

    # Save the complete preprocessing + Random Forest pipeline
    joblib.dump(pipeline, MODEL_PATH)

    print()
    print("=" * 50)
    print("MODEL SAVED")
    print("=" * 50)

    print(MODEL_PATH)


if __name__ == "__main__":
    main()