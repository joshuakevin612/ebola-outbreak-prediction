import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


TARGET = "Target_Label"
ID_COL = "Patient_ID"

CATEGORICAL = [
    "Gender",
    "Occupation",
    "Region",
    "Urban_Rural",
    "Immune_Condition"
]


def load_data(path):
    return pd.read_csv(path)


def split_xy(df):
    """
    Separate the input features (X) from the target (y).

    Negative = 0
    Positive = 1
    """

    y = df[TARGET].map({
        "Negative": 0,
        "Positive": 1
    })

    if y.isna().any():
        raise ValueError(
            "Target_Label contains values other than Positive/Negative"
        )

    X = df.drop(columns=[TARGET, ID_COL])

    return X, y


def build_preprocessor():
    """
    Convert categorical text columns into numerical columns.
    Leave numerical and 0/1 columns unchanged.
    """

    return ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False
                ),
                CATEGORICAL
            )
        ],
        remainder="passthrough",
        verbose_feature_names_out=False
    )
