"""
Shared ARIMA + LSTM forecasting logic for the Ebola multisource project.
Used by both forecast_pipeline.py (CLI) and app.py (Streamlit frontend).
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

DATASETS = {
    "West Africa (2014-2016)": {
        "csv": "west_africa_ebola_2014_2016_clean.csv",
        "cumulative_col": "cases_WestAfrica_total",
        "freq": "D",
        "lookback": 14,
        "active_end": "2015-11-26",  # trims the dead reporting-gap tail
    },
    "DRC North Kivu / Ituri (2018-2020)": {
        "csv": "drc_kivu_ebola_clean.csv",
        "cumulative_col": None,  # already a "new cases" weekly count
        "value_col": "new_cases_national",
        "freq": "W-SUN",
        "lookback": 6,
        "active_end": None,
    },
}


def load_series(dataset_key: str, data_dir: str = ".") -> pd.Series:
    """Load one of the two cleaned datasets and return a regular-frequency
    'new cases' time series indexed by date."""
    cfg = DATASETS[dataset_key]
    df = pd.read_csv(f"{data_dir}/{cfg['csv']}", parse_dates=["date"]).sort_values("date")

    if cfg["active_end"]:
        df = df[df["date"] <= cfg["active_end"]]

    if cfg["cumulative_col"]:
        df["new_cases"] = df[cfg["cumulative_col"]].diff().clip(lower=0)
        df = df.dropna(subset=["new_cases"])
        value_col = "new_cases"
    else:
        value_col = cfg["value_col"]

    series = df.set_index("date")[value_col].asfreq(cfg["freq"]).interpolate()
    return series


def adf_test(series: pd.Series) -> dict:
    stat, p = adfuller(series.dropna())[:2]
    return {"stat": stat, "p_value": p, "stationary": p < 0.05}


def chronological_split(series: pd.Series, test_frac: float = 0.2):
    split_idx = int(len(series) * (1 - test_frac))
    return series.iloc[:split_idx], series.iloc[split_idx:]


def fit_arima(train: pd.Series, test_len: int, max_p=3, max_q=3):
    """Small grid search over (p,d,q) by AIC, then forecast test_len steps ahead."""
    best_aic, best_order, best_fit = np.inf, None, None
    for p in range(0, max_p + 1):
        for d in (0, 1):
            for q in range(0, max_q + 1):
                try:
                    fit = ARIMA(train, order=(p, d, q)).fit()
                    if fit.aic < best_aic:
                        best_aic, best_order, best_fit = fit.aic, (p, d, q), fit
                except Exception:
                    continue
    forecast = best_fit.forecast(steps=test_len)
    return {"order": best_order, "aic": best_aic, "forecast": forecast, "model": best_fit}


def _make_windows(arr, lookback):
    X, y = [], []
    for i in range(lookback, len(arr)):
        X.append(arr[i - lookback:i, 0])
        y.append(arr[i, 0])
    return np.array(X), np.array(y)


def _build_lstm_model(lookback):
    model = Sequential([
        LSTM(64, activation="tanh", return_sequences=True, input_shape=(lookback, 1)),
        Dropout(0.2),
        LSTM(32, activation="tanh"),
        Dropout(0.2),
        Dense(16, activation="relu"),
        Dense(1),
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


def fit_lstm(series: pd.Series, split_idx: int, lookback: int, epochs=100, seed=42,
             progress_cb=None, log_transform=True):
    """Train an LSTM on the train portion of `series` and forecast the test portion.
    progress_cb, if given, is called with (epoch, total_epochs, loss) during training.

    log_transform=True (default, FIX #1) applies log1p before scaling and expm1
    after inverse-scaling. Outbreak case counts span near-zero to thousands, which
    badly distorts plain min-max scaling and blows up relative error (R2) on the
    low-count tail of a series. Log-transforming compresses that range and is
    standard practice for count data like this.
    """
    tf.random.set_seed(seed)
    np.random.seed(seed)

    raw = series.values.reshape(-1, 1).astype(float)
    working = np.log1p(raw) if log_transform else raw

    scaler = MinMaxScaler()
    scaler.fit(working[:split_idx])
    full_scaled = scaler.transform(working)

    X_all, y_all = _make_windows(full_scaled, lookback)
    cut = split_idx - lookback
    X_train, y_train = X_all[:cut], y_all[:cut]
    X_test, y_test = X_all[cut:], y_all[cut:]

    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
    X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

    model = _build_lstm_model(lookback)

    callbacks = [EarlyStopping(monitor="loss", patience=10, restore_best_weights=True)]
    if progress_cb:
        class _CB(tf.keras.callbacks.Callback):
            def on_epoch_end(self, epoch, logs=None):
                progress_cb(epoch + 1, epochs, logs.get("loss"))
        callbacks.append(_CB())

    model.fit(X_train, y_train, epochs=epochs, batch_size=8, verbose=0, callbacks=callbacks)

    pred_scaled = model.predict(X_test, verbose=0)
    pred = scaler.inverse_transform(pred_scaled)
    pred = np.expm1(pred) if log_transform else pred
    return pred.flatten(), model


def fit_lstm_pooled(train_series: dict, test_series: dict, lookback: int,
                     epochs=100, seed=42, progress_cb=None, log_transform=True):
    """FIX #3: train ONE LSTM on windows pooled from multiple series' train
    portions (so it sees more examples of 'how an outbreak curve behaves' than
    any single series alone provides), then forecast each series' own test
    portion separately with that shared model.

    train_series / test_series: dicts of {name: pd.Series}, same keys in both.
    A separate scaler is still fit on each series' OWN train data (pooling the
    windows, not the raw scale, since the two outbreaks have very different
    case-count magnitudes).
    Returns: {name: forecast_array}, model
    """
    tf.random.set_seed(seed)
    np.random.seed(seed)

    scalers = {}
    X_train_all, y_train_all = [], []
    for name, train in train_series.items():
        raw = train.values.reshape(-1, 1).astype(float)
        working = np.log1p(raw) if log_transform else raw
        scaler = MinMaxScaler().fit(working)
        scalers[name] = scaler
        scaled = scaler.transform(working)
        X, y = _make_windows(scaled, lookback)
        if len(X):
            X_train_all.append(X)
            y_train_all.append(y)

    X_train = np.concatenate(X_train_all).reshape(-1, lookback, 1)
    y_train = np.concatenate(y_train_all)

    model = _build_lstm_model(lookback)
    callbacks = [EarlyStopping(monitor="loss", patience=10, restore_best_weights=True)]
    if progress_cb:
        class _CB(tf.keras.callbacks.Callback):
            def on_epoch_end(self, epoch, logs=None):
                progress_cb(epoch + 1, epochs, logs.get("loss"))
        callbacks.append(_CB())
    model.fit(X_train, y_train, epochs=epochs, batch_size=8, verbose=0, callbacks=callbacks)

    forecasts = {}
    for name, test in test_series.items():
        full = pd.concat([train_series[name], test])
        raw = full.values.reshape(-1, 1).astype(float)
        working = np.log1p(raw) if log_transform else raw
        scaled = scalers[name].transform(working)
        X_all, _ = _make_windows(scaled, lookback)
        split_point = len(train_series[name]) - lookback
        X_test = X_all[split_point:].reshape(-1, lookback, 1)
        pred_scaled = model.predict(X_test, verbose=0)
        pred = scalers[name].inverse_transform(pred_scaled)
        pred = np.expm1(pred) if log_transform else pred
        forecasts[name] = pred.flatten()

    return forecasts, model


def naive_forecast(train: pd.Series, test_len: int, method="last") -> np.ndarray:
    """FIX #4: dumb baselines to sanity-check ARIMA/LSTM against.
    method='last' -> repeat the final training value for every test step.
    method='moving_avg' -> repeat the mean of the last 7 training points.
    If ARIMA/LSTM can't beat this, that's a real finding worth reporting."""
    if method == "last":
        value = train.values[-1]
    elif method == "moving_avg":
        value = train.values[-7:].mean()
    else:
        raise ValueError("method must be 'last' or 'moving_avg'")
    return np.full(test_len, value)


def evaluate(y_true, y_pred) -> dict:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }
