"""
ARIMA + LSTM forecasting pipeline for Ebola new-case counts — Phase 1 improved.

Compares FOUR approaches on the same held-out test window per dataset:
  1. Naive baseline (7-point moving average)
  2. ARIMA
  3. LSTM (log-transformed, single-series)
  4. LSTM (log-transformed, trained on BOTH outbreaks pooled)

Outputs:
  - forecast_comparison.png   (all four, overlaid on the held-out test set)
  - metrics printed to stdout for every dataset
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from forecasting import (
    DATASETS, load_series, adf_test, chronological_split,
    fit_arima, fit_lstm, fit_lstm_pooled, naive_forecast, evaluate,
)

LSTM_EPOCHS = 100
TEST_FRAC = 0.2

# ---------------------------------------------------------------
# 1. LOAD BOTH SERIES (needed up front now, for the pooled LSTM)
# ---------------------------------------------------------------
series_by_name = {key: load_series(key) for key in DATASETS}
train_by_name, test_by_name = {}, {}
for key, s in series_by_name.items():
    train_by_name[key], test_by_name[key] = chronological_split(s, TEST_FRAC)
    print(f"{key}: {len(s)} points | train {len(train_by_name[key])} | test {len(test_by_name[key])}")

# ---------------------------------------------------------------
# 2. POOLED LSTM — trained once, on BOTH outbreaks' train portions
# ---------------------------------------------------------------
print("\n--- Training pooled LSTM (both outbreaks combined) ---")
pooled_lookback = min(DATASETS[k]["lookback"] for k in DATASETS)  # shared window size across series
pooled_forecasts, _ = fit_lstm_pooled(
    train_by_name, test_by_name, lookback=pooled_lookback, epochs=LSTM_EPOCHS
)

# ---------------------------------------------------------------
# 3. PER-DATASET: naive baseline, ARIMA, single-series LSTM
# ---------------------------------------------------------------
results = {}  # {dataset_key: {"train":..,"test":..,"forecasts":{method: array}}}

for key in DATASETS:
    print(f"\n=== {key} ===")
    series = series_by_name[key]
    train, test = train_by_name[key], test_by_name[key]
    lookback = DATASETS[key]["lookback"]

    adf = adf_test(series)
    print(f"ADF: stat={adf['stat']:.3f} p={adf['p_value']:.4f} -> "
          f"{'stationary' if adf['stationary'] else 'non-stationary (ARIMA handles via differencing)'}")

    forecasts = {}

    # --- naive baseline ---
    forecasts["naive_moving_avg"] = naive_forecast(train, len(test), method="moving_avg")

    # --- ARIMA ---
    arima_result = fit_arima(train, len(test))
    print(f"Best ARIMA order: {arima_result['order']} (AIC={arima_result['aic']:.1f})")
    forecasts["arima"] = arima_result["forecast"].values

    # --- single-series LSTM (log-transformed) ---
    split_idx = len(train)
    lstm_pred, _ = fit_lstm(series, split_idx, lookback, epochs=LSTM_EPOCHS, log_transform=True)
    forecasts["lstm_single"] = lstm_pred

    # --- pooled LSTM (already computed above) ---
    forecasts["lstm_pooled"] = pooled_forecasts[key]

    # --- evaluate everything on the same test window ---
    print(f"\n{'Method':<16s} {'RMSE':>8s} {'MAE':>8s} {'R2':>8s}")
    for method, pred in forecasts.items():
        n = min(len(test), len(pred))
        m = evaluate(test.values[:n], pred[:n])
        print(f"{method:<16s} {m['rmse']:8.2f} {m['mae']:8.2f} {m['r2']:8.3f}")

    results[key] = {"train": train, "test": test, "forecasts": forecasts}

# ---------------------------------------------------------------
# 4. PLOT — one panel per dataset
# ---------------------------------------------------------------
fig, axes = plt.subplots(len(DATASETS), 1, figsize=(12, 5 * len(DATASETS)))
if len(DATASETS) == 1:
    axes = [axes]

colors = {"naive_moving_avg": "tab:gray", "arima": "tab:blue",
          "lstm_single": "tab:orange", "lstm_pooled": "tab:green"}
labels = {"naive_moving_avg": "Naive (7pt avg)", "arima": "ARIMA",
          "lstm_single": "LSTM (single)", "lstm_pooled": "LSTM (pooled)"}

for ax, (key, r) in zip(axes, results.items()):
    train, test = r["train"], r["test"]
    tail = min(len(train), 60)
    ax.plot(train.index[-tail:], train.values[-tail:], label="Train (recent)", color="black", alpha=0.3)
    ax.plot(test.index, test.values, label="Actual", color="black", linewidth=2)
    for method, pred in r["forecasts"].items():
        n = min(len(test), len(pred))
        ax.plot(test.index[:n], pred[:n], "--", label=labels[method], color=colors[method])
    ax.set_title(key)
    ax.set_ylabel("New cases")
    ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig("forecast_comparison.png", dpi=150)
print("\nSaved plot -> forecast_comparison.png")
