"""
Streamlit dashboard for the AI-Driven Multisource Ebola Outbreak Prediction
project — forecasting front-end (ARIMA vs LSTM) on top of forecasting.py.

Run with:  streamlit run app.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from forecasting import (
    DATASETS, load_series, adf_test, chronological_split,
    fit_arima, fit_lstm, fit_lstm_pooled, naive_forecast, evaluate,
)

st.set_page_config(page_title="Ebola Outbreak Forecasting", layout="wide")

st.title("🦠 Ebola Outbreak Forecasting — ARIMA vs LSTM")
st.caption(
    "AI-Driven Multisource Ebola Outbreak Prediction Model — forecasting module. "
    "Pick an outbreak dataset, split it chronologically, and compare a classical "
    "statistical model (ARIMA) against a deep-learning model (LSTM) on the same held-out test window."
)

# ----------------------------------------------------------------
# SIDEBAR — controls
# ----------------------------------------------------------------
with st.sidebar:
    st.header("Settings")
    dataset_key = st.selectbox("Dataset", list(DATASETS.keys()))
    test_frac = st.slider("Test set size (fraction of series)", 0.1, 0.4, 0.2, 0.05)
    max_p = st.slider("ARIMA max p / q (search grid)", 1, 4, 3)
    lstm_epochs = st.slider("LSTM epochs", 20, 200, 100, 10)
    default_lookback = DATASETS[dataset_key]["lookback"]
    lookback = st.slider(
        "LSTM lookback window (time steps)", 3, 30, default_lookback,
        help="How many past days/weeks the LSTM sees before predicting the next point.",
    )
    include_naive = st.checkbox("Include naive baseline (7-point moving average)", value=True)
    include_pooled = st.checkbox(
        "Include pooled LSTM (trained on BOTH outbreaks combined)", value=True,
        help="Trains one LSTM on windows from both datasets' train portions, then "
             "forecasts this dataset's test window — usually helps on the smaller DRC series.",
    )
    run = st.button("Run forecast", type="primary", use_container_width=True)

# ----------------------------------------------------------------
# LOAD + DESCRIBE SERIES
# ----------------------------------------------------------------
series = load_series(dataset_key)
unit = "day" if DATASETS[dataset_key]["freq"] == "D" else "week"

col1, col2, col3 = st.columns(3)
col1.metric("Series length", f"{len(series)} {unit}s")
col2.metric("Date range", f"{series.index.min().date()} → {series.index.max().date()}")
col3.metric("Peak new cases", f"{series.max():.0f}")

st.subheader("Raw series")
fig0, ax0 = plt.subplots(figsize=(10, 3))
ax0.plot(series.index, series.values, color="#444")
ax0.set_ylabel(f"New cases / {unit}")
st.pyplot(fig0)

if dataset_key.startswith("West Africa"):
    st.info(
        "This series is trimmed to end 2015-11-26 — after that the cumulative "
        "count flatlines (reporting gap) and one late entry is a downward "
        "case-count revision, not new cases. Including that dead tail would "
        "make any split land on near-zero variance and give meaningless metrics."
    )

adf = adf_test(series)
st.write(
    f"**ADF stationarity test:** stat = {adf['stat']:.3f}, p = {adf['p_value']:.4f} → "
    f"{'series is stationary' if adf['stationary'] else 'series is non-stationary (ARIMA differencing will handle this)'}"
)

# ----------------------------------------------------------------
# RUN MODELS
# ----------------------------------------------------------------
if run:
    train, test = chronological_split(series, test_frac)
    st.write(f"Training on **{len(train)}** points, testing on the most recent **{len(test)}** points (no shuffling).")

    forecasts = {}  # method label -> np.array aligned to test.index[:len]

    if include_naive:
        forecasts["Naive (7pt avg)"] = naive_forecast(train, len(test), method="moving_avg")

    with st.spinner("Fitting ARIMA (grid search over orders)…"):
        arima_result = fit_arima(train, len(test), max_p=max_p, max_q=max_p)
    st.success(f"Best ARIMA order: {arima_result['order']} (AIC = {arima_result['aic']:.1f})")
    forecasts[f"ARIMA{arima_result['order']}"] = arima_result["forecast"].values

    progress_bar = st.progress(0.0, text="Training LSTM (single-series)…")
    def _progress(epoch, total, loss):
        progress_bar.progress(epoch / total, text=f"Training LSTM — epoch {epoch}/{total} (loss={loss:.4f})")

    split_idx = len(train)
    lstm_pred, _ = fit_lstm(series, split_idx, lookback, epochs=lstm_epochs, progress_cb=_progress)
    progress_bar.empty()
    forecasts["LSTM (single)"] = lstm_pred

    if include_pooled:
        other_keys = [k for k in DATASETS if k != dataset_key]
        pooled_progress = st.progress(0.0, text="Training pooled LSTM (both outbreaks)…")
        def _pooled_progress(epoch, total, loss):
            pooled_progress.progress(epoch / total, text=f"Pooled LSTM — epoch {epoch}/{total} (loss={loss:.4f})")

        all_series = {k: load_series(k) for k in DATASETS}
        train_by_name, test_by_name = {}, {}
        for k, s in all_series.items():
            tr, te = chronological_split(s, test_frac)
            train_by_name[k], test_by_name[k] = tr, te
        pooled_lookback = min(DATASETS[k]["lookback"] for k in DATASETS)
        pooled_forecasts, _ = fit_lstm_pooled(
            train_by_name, test_by_name, lookback=pooled_lookback,
            epochs=lstm_epochs, progress_cb=_pooled_progress,
        )
        pooled_progress.empty()
        forecasts["LSTM (pooled)"] = pooled_forecasts[dataset_key]

    st.subheader("Results")
    metrics_rows = {}
    for label, pred in forecasts.items():
        n = min(len(test), len(pred))
        metrics_rows[label] = evaluate(test.values[:n], pred[:n])
    metrics_df = pd.DataFrame(metrics_rows).T.rename(columns={"rmse": "RMSE", "mae": "MAE", "r2": "R²"})
    st.dataframe(metrics_df.style.format("{:.3f}"), use_container_width=True)

    fig, ax = plt.subplots(figsize=(11, 4.5))
    tail = min(len(train), 12 if unit == "week" else 60)
    ax.plot(train.index[-tail:], train.values[-tail:], label=f"Train (last {tail} {unit}s)", color="gray")
    ax.plot(test.index, test.values, label="Actual", color="black", linewidth=2)
    for label, pred in forecasts.items():
        n = min(len(test), len(pred))
        ax.plot(test.index[:n], pred[:n], "--", label=label)
    ax.set_ylabel(f"New cases / {unit}")
    ax.legend()
    st.pyplot(fig)

    with st.expander("How to read this"):
        st.markdown(
            "- **RMSE / MAE** — average prediction error in raw case counts; lower is better.\n"
            "- **R²** — how much of the test-set variance the model explains; 1.0 is perfect, "
            "0 means 'no better than predicting the mean', and negative means worse than that. "
            "On short, noisy outbreak tails negative R² is common across all methods here — "
            "that's a genuine finding worth reporting, not a bug.\n"
            "- **Naive baseline** — repeats the last 7-point average forward. If ARIMA/LSTM "
            "can't beat this, that itself is worth reporting.\n"
            "- **LSTM (pooled)** is trained on windows from BOTH outbreaks' training data at once, "
            "then forecasts just this dataset's test window — it tends to help most on the smaller "
            "DRC series, where a single-series LSTM has very little data to learn from.\n"
            "- Case counts are log-transformed before scaling for both LSTM variants — this keeps "
            "near-zero-count periods from blowing up the error metrics."
        )

    # download predictions
    out = pd.DataFrame({"date": test.index, "actual": test.values}).set_index("date")
    for label, pred in forecasts.items():
        n = min(len(test), len(pred))
        out.loc[out.index[:n], label] = pred[:n]
    st.download_button(
        "Download forecast results (CSV)",
        out.to_csv().encode(),
        file_name=f"forecast_results_{dataset_key.split()[0].lower()}.csv",
        mime="text/csv",
    )
else:
    st.info("Set your options in the sidebar and click **Run forecast**.")
