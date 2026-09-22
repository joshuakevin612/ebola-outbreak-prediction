"""
ARIMA + LSTM forecasting pipeline for Ebola daily new-case counts.
Works on either cleaned dataset (west_africa_ebola_2014_2016_clean.csv
or drc_kivu_ebola_clean.csv) — point TARGET_CSV / TARGET_COL at the one you want.

Outputs:
  - forecast_comparison.png   (ARIMA vs LSTM vs actual, on the held-out test set)
  - metrics printed to stdout (RMSE, MAE, R2 for both models)
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

tf.random.set_seed(42)
np.random.seed(42)

# ---------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------
# Set DATASET = "west_africa" or "drc" to switch which outbreak you forecast.
DATASET = "drc"

if DATASET == "west_africa":
    TARGET_CSV, CUM_COL, FREQ, LOOKBACK = "west_africa_ebola_2014_2016_clean.csv", "cases_WestAfrica_total", "D", 14
    df = pd.read_csv(TARGET_CSV, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    # The West Africa cumulative count flatlines from ~2015-11-26 onward (reporting
    # essentially stopped, and the lone Mar-2016 entry is a downward case-count
    # revision, not new cases). That dead tail has ~zero variance and would make
    # any train/test split landing in it trivially "perfect" and meaningless, so
    # we trim the series to the period with active, frequent reporting.
    df = df[df["date"] <= "2015-11-26"].reset_index(drop=True)
    df["new_cases"] = df[CUM_COL].diff().clip(lower=0)
    df = df.dropna(subset=["new_cases"]).reset_index(drop=True)
    series = df.set_index("date")["new_cases"].asfreq("D").interpolate()
else:
    # DRC North Kivu/Ituri outbreak (2018-2020), already weekly, already a
    # "new cases" count (not cumulative) — no diff/interpolation needed.
    TARGET_CSV, FREQ, LOOKBACK = "drc_kivu_ebola_clean.csv", "W", 6
    df = pd.read_csv(TARGET_CSV, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    series = df.set_index("date")["new_cases_national"].asfreq("W-SUN").interpolate()

print(f"Series length: {len(series)} {'days' if FREQ=='D' else 'weeks'}, "
      f"{series.index.min().date()} -> {series.index.max().date()}")

# ---------------------------------------------------------------
# 2. STATIONARITY CHECK (informs ARIMA's 'd' term)
# ---------------------------------------------------------------
adf_stat, adf_p = adfuller(series.dropna())[:2]
print(f"ADF test on raw series: stat={adf_stat:.3f}, p={adf_p:.4f} -> "
      f"{'stationary' if adf_p < 0.05 else 'non-stationary (differencing needed)'}")

# ---------------------------------------------------------------
# 3. CHRONOLOGICAL TRAIN/TEST SPLIT (80/20, no shuffling)
# ---------------------------------------------------------------
split_idx = int(len(series) * 0.8)
train, test = series.iloc[:split_idx], series.iloc[split_idx:]
print(f"Train: {len(train)} days | Test: {len(test)} days")

# =================================================================
# MODEL A — ARIMA
# =================================================================
best_aic, best_order, best_fit = np.inf, None, None
for p in range(0, 4):
    for d in (0, 1):
        for q in range(0, 4):
            try:
                fit = ARIMA(train, order=(p, d, q)).fit()
                if fit.aic < best_aic:
                    best_aic, best_order, best_fit = fit.aic, (p, d, q), fit
            except Exception:
                continue

print(f"Best ARIMA order: {best_order} (AIC={best_aic:.1f})")
arima_forecast = best_fit.forecast(steps=len(test))
arima_forecast.index = test.index

# =================================================================
# MODEL B — LSTM
# =================================================================
LOOKBACK = 14  # use the past 14 days to predict the next day

scaler = MinMaxScaler()
train_scaled = scaler.fit_transform(train.values.reshape(-1, 1))
# scale test using train's scaler (no leakage), but LSTM needs LOOKBACK days
# of history immediately preceding the test set too:
full_scaled = scaler.transform(series.values.reshape(-1, 1))

def make_windows(arr, lookback):
    X, y = [], []
    for i in range(lookback, len(arr)):
        X.append(arr[i - lookback:i, 0])
        y.append(arr[i, 0])
    return np.array(X), np.array(y)

X_all, y_all = make_windows(full_scaled, LOOKBACK)
# indices in X_all/y_all line up with series[LOOKBACK:]
split_point = split_idx - LOOKBACK
X_train, y_train = X_all[:split_point], y_all[:split_point]
X_test, y_test = X_all[split_point:], y_all[split_point:]

X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

model = Sequential([
    LSTM(64, activation="tanh", return_sequences=True, input_shape=(LOOKBACK, 1)),
    Dropout(0.2),
    LSTM(32, activation="tanh"),
    Dropout(0.2),
    Dense(16, activation="relu"),
    Dense(1),
])
model.compile(optimizer="adam", loss="mse")

es = EarlyStopping(monitor="loss", patience=10, restore_best_weights=True)
model.fit(X_train, y_train, epochs=100, batch_size=8, verbose=0, callbacks=[es])

lstm_pred_scaled = model.predict(X_test, verbose=0)
lstm_forecast = scaler.inverse_transform(lstm_pred_scaled).flatten()
lstm_forecast = pd.Series(lstm_forecast, index=test.index[:len(lstm_forecast)])

# =================================================================
# 4. EVALUATE BOTH MODELS ON THE SAME TEST WINDOW
# =================================================================
def report(name, y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    print(f"{name:>8s} -> RMSE={rmse:8.2f}  MAE={mae:8.2f}  R2={r2:6.3f}")
    return rmse, mae, r2

print("\n--- Test-set performance ---")
report("ARIMA", test.values, arima_forecast.values)
report("LSTM", test.values[:len(lstm_forecast)], lstm_forecast.values)

# =================================================================
# 5. PLOT
# =================================================================
plt.figure(figsize=(12, 5))
plt.plot(train.index[-60:], train.values[-60:], label="Train (last 60d)", color="gray")
plt.plot(test.index, test.values, label="Actual", color="black", linewidth=2)
plt.plot(arima_forecast.index, arima_forecast.values, label=f"ARIMA{best_order}", linestyle="--")
plt.plot(lstm_forecast.index, lstm_forecast.values, label="LSTM", linestyle="--")
plt.title("Ebola daily new cases — ARIMA vs LSTM forecast on held-out test set")
plt.xlabel("Date")
plt.ylabel("New cases")
plt.legend()
plt.tight_layout()
plt.savefig("forecast_comparison.png", dpi=150)
print("\nSaved plot -> forecast_comparison.png")
