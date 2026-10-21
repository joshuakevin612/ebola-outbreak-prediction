"""
Professional dashboard for the AI-Driven Multisource Ebola
Outbreak Prediction project.

Compares ARIMA, LSTM, pooled LSTM, and a naive baseline.
Research prototype only — not a clinical decision-making tool.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from forecasting import (
    DATASETS,
    load_series,
    adf_test,
    chronological_split,
    fit_arima,
    fit_lstm,
    fit_lstm_pooled,
    naive_forecast,
    evaluate,
    TENSORFLOW_AVAILABLE,
)

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Ebola Forecasting | AI Research Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Ebola Outbreak Forecasting")

st.caption(
    "AI-driven multisource research dashboard | "
    "Statistical and deep-learning model comparison"
)

st.markdown(
    "Explore historical outbreak trends, configure forecasting "
    "experiments, and compare predictions against reported cases."
)

st.divider()

# ---------------------------------------------------------
# SINGLE SIDEBAR
# ---------------------------------------------------------
with st.sidebar:
    st.title("Forecast Controls")
    st.caption("Configure your experiment")

    st.subheader("Dataset")

    dataset_key = st.selectbox(
        "Outbreak dataset",
        list(DATASETS.keys()),
        help="Choose the historical outbreak to analyse.",
    )

    st.divider()
    st.subheader("Evaluation")

    test_frac = st.slider(
        "Test set proportion",
        min_value=0.1,
        max_value=0.4,
        value=0.2,
        step=0.05,
        help=(
            "Fraction of the latest observations reserved for testing. "
            "The split remains chronological."
        ),
    )

    st.divider()
    st.subheader("ARIMA configuration")

    max_p = st.slider(
        "Maximum ARIMA p and q",
        min_value=1,
        max_value=4,
        value=3,
        help=(
            "Searches p and q from zero to this maximum. "
            "Differencing order d is tested at 0 and 1."
        ),
    )

    st.divider()
    st.subheader("LSTM configuration")

    lstm_epochs = st.slider(
        "Training epochs",
        min_value=20,
        max_value=200,
        value=100,
        step=10,
        disabled=not TENSORFLOW_AVAILABLE,
        help=(
            "Maximum training epochs; early stopping may end "
            "training sooner."
        ),
    )

    default_lookback = DATASETS[dataset_key]["lookback"]

    lookback = st.slider(
        "Lookback window",
        min_value=3,
        max_value=30,
        value=default_lookback,
        disabled=not TENSORFLOW_AVAILABLE,
        help="Number of previous time steps used as LSTM input.",
    )

    st.divider()
    st.subheader("Models to compare")

    include_naive = st.checkbox(
        "Naive moving-average baseline",
        value=True,
    )

    include_arima = st.checkbox(
        "ARIMA statistical model",
        value=True,
    )

    include_lstm = st.checkbox(
        "Single-series LSTM",
        value=True,
        disabled=not TENSORFLOW_AVAILABLE,
    )

    include_pooled = st.checkbox(
        "Pooled LSTM",
        value=True,
        disabled=not TENSORFLOW_AVAILABLE,
        help="Trains one LSTM using training data from both outbreaks.",
    )

    st.divider()

    run = st.button(
        "Run forecast",
        type="primary",
        use_container_width=True,
    )

    st.caption("Research prototype — not for clinical diagnosis.")

if not TENSORFLOW_AVAILABLE:
    st.warning(
        "TensorFlow could not be loaded. ARIMA and the naive baseline "
        "remain available; LSTM models are disabled for this session."
    )

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
try:
    series = load_series(dataset_key)

except Exception as exc:
    st.error(f"Could not load the selected dataset: {exc}")
    st.stop()

if series.empty:
    st.error("The selected dataset contains no usable observations.")
    st.stop()

series = series.sort_index()

if not np.isfinite(series.to_numpy(dtype=float)).all():
    st.error(
        "The time series contains missing or non-finite values. "
        "Check the dataset and preprocessing."
    )
    st.stop()

if (series < 0).any():
    st.warning(
        "Negative case counts were found. Review the source data "
        "before interpreting model results."
    )

unit = "day" if DATASETS[dataset_key]["freq"] == "D" else "week"

# ---------------------------------------------------------
# DATASET OVERVIEW
# ---------------------------------------------------------
st.subheader("Dataset overview")

col1, col2, col3 = st.columns(3)

col1.metric("Observations", f"{len(series):,}")

col2.metric(
    "Date range",
    f"{series.index.min().date()} — {series.index.max().date()}",
)

col3.metric(
    "Peak reported new cases",
    f"{series.max():,.0f}",
)

with st.expander("Dataset information"):
    st.write(f"**Selected outbreak:** {dataset_key}")
    st.write(f"**Frequency:** One observation per {unit}")
    st.write(f"**Number of observations:** {len(series):,}")

    st.write(
        "Forecast quality depends on reporting completeness, "
        "case definitions, preprocessing, and source-data quality."
    )

if dataset_key.startswith("West Africa"):
    st.info(
        "The data loader trims this series to 26 November 2015. "
        "Review reporting gaps and revisions before interpreting "
        "the forecast."
    )

# ---------------------------------------------------------
# HISTORICAL TREND
# ---------------------------------------------------------
st.subheader("Historical outbreak trend")

fig, ax = plt.subplots(figsize=(12, 4))

ax.plot(
    series.index,
    series.values,
    color="#2563EB",
    linewidth=1.8,
    label="Reported new cases",
)

ax.set_xlabel("Date")
ax.set_ylabel(f"New cases per {unit}")
ax.grid(True, alpha=0.25)
ax.legend()

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ---------------------------------------------------------
# STATISTICAL DIAGNOSTICS
# ---------------------------------------------------------
st.subheader("Statistical diagnostics")

try:
    adf = adf_test(series)

    d1, d2, d3 = st.columns(3)

    d1.metric("ADF statistic", f"{adf['stat']:.3f}")
    d2.metric("ADF p-value", f"{adf['p_value']:.4f}")

    d3.metric(
        "Stationarity at 5%",
        "Evidence of stationarity"
        if adf["stationary"]
        else "Not established",
    )

    st.caption(
        "The Augmented Dickey–Fuller test assesses evidence against "
        "a unit root. It does not identify the most accurate model."
    )

except Exception as exc:
    st.warning(f"Stationarity test could not be completed: {exc}")

st.divider()

# ---------------------------------------------------------
# RUN FORECASTS
# ---------------------------------------------------------
if not run:
    st.info(
        "Choose your dataset and model settings in the sidebar, "
        "then click **Run forecast**."
    )
    st.stop()

train, test = chronological_split(series, test_frac)

if len(train) < 10 or len(test) < 1:
    st.error("Insufficient observations for the selected test split.")
    st.stop()

st.subheader("Forecast experiment")

st.write(
    f"Training observations: **{len(train):,}**  |  "
    f"Test observations: **{len(test):,}**  |  "
    f"Test period: **{test.index.min().date()} to "
    f"{test.index.max().date()}**"
)

forecasts = {}

# ---------------------------------------------------------
# NAIVE BASELINE
# ---------------------------------------------------------
if include_naive:
    try:
        forecasts["Naive (7-point average)"] = naive_forecast(
            train,
            len(test),
            method="moving_avg",
        )

    except Exception as exc:
        st.error(f"Naive baseline failed: {exc}")

# ---------------------------------------------------------
# ARIMA
# ---------------------------------------------------------
if include_arima:
    try:
        with st.spinner("Searching ARIMA configurations..."):
            result = fit_arima(
                train,
                len(test),
                max_p=max_p,
                max_q=max_p,
            )

        if result["forecast"] is not None:
            forecasts[f"ARIMA {result['order']}"] = np.asarray(
                result["forecast"],
                dtype=float,
            ).ravel()

            st.success(
                f"Selected ARIMA order: {result['order']} "
                f"| AIC: {result['aic']:.2f}"
            )

        else:
            st.error("ARIMA did not produce a valid forecast.")

    except Exception as exc:
        st.error(f"ARIMA failed: {exc}")

# ---------------------------------------------------------
# SINGLE-SERIES LSTM
# ---------------------------------------------------------
if include_lstm and TENSORFLOW_AVAILABLE:
    try:
        progress = st.progress(
            0.0,
            text="Training single-series LSTM...",
        )

        def update_progress(epoch, total, loss):
            loss_text = f"{loss:.4f}" if loss is not None else "N/A"

            progress.progress(
                min(epoch / total, 1.0),
                text=f"LSTM epoch {epoch}/{total} | loss {loss_text}",
            )

        prediction, _ = fit_lstm(
            series,
            len(train),
            lookback,
            epochs=lstm_epochs,
            progress_cb=update_progress,
        )

        progress.empty()

        forecasts["LSTM (single-series)"] = np.asarray(
            prediction,
            dtype=float,
        ).ravel()

    except Exception as exc:
        st.error(f"Single-series LSTM failed: {exc}")

# ---------------------------------------------------------
# POOLED LSTM
# ---------------------------------------------------------
if include_pooled and TENSORFLOW_AVAILABLE:
    try:
        with st.spinner("Training pooled LSTM..."):
            all_series = {
                key: load_series(key)
                for key in DATASETS
            }

            train_by_name = {}
            test_by_name = {}

            for key, current_series in all_series.items():
                tr, te = chronological_split(
                    current_series,
                    test_frac,
                )

                train_by_name[key] = tr
                test_by_name[key] = te

            pooled_lookback = min(
                DATASETS[key]["lookback"]
                for key in DATASETS
            )

            pooled_predictions, _ = fit_lstm_pooled(
                train_by_name,
                test_by_name,
                lookback=pooled_lookback,
                epochs=lstm_epochs,
            )

        if dataset_key in pooled_predictions:
            forecasts["LSTM (pooled)"] = np.asarray(
                pooled_predictions[dataset_key],
                dtype=float,
            ).ravel()

    except Exception as exc:
        st.error(f"Pooled LSTM failed: {exc}")

# ---------------------------------------------------------
# EVALUATION
# ---------------------------------------------------------
if not forecasts:
    st.error(
        "No model produced a forecast. Enable a model and review "
        "any errors displayed above."
    )
    st.stop()

actual = test.to_numpy(dtype=float)

metric_rows = []
prediction_columns = {}

for label, prediction in forecasts.items():
    prediction = np.asarray(
        prediction,
        dtype=float,
    ).ravel()

    n = min(len(actual), len(prediction))

    if n == 0:
        st.warning(f"{label} produced no predictions.")
        continue

    y_true = actual[:n]
    y_pred = prediction[:n]

    try:
        metrics = evaluate(y_true, y_pred)

        # Only the requested four columns are included.
        metric_rows.append({
            "Model": label,
            "RMSE": metrics["rmse"],
            "MAE": metrics["mae"],
            "R²": metrics["r2"],
        })

        prediction_columns[label] = (n, y_pred)

    except Exception as exc:
        st.warning(f"Could not evaluate {label}: {exc}")

if not metric_rows:
    st.error("No valid model metrics could be calculated.")
    st.stop()

comparison_df = pd.DataFrame(metric_rows)

# ---------------------------------------------------------
# MODEL COMPARISON TABLE + CSV DOWNLOAD
# ---------------------------------------------------------
st.subheader("Model Comparison")

st.caption(
    "Lower RMSE and MAE are generally better. "
    "Higher R² is generally better."
)

st.dataframe(
    comparison_df.style.format(
        {
            "RMSE": "{:.4f}",
            "MAE": "{:.4f}",
            "R²": "{:.4f}",
        },
        na_rep="N/A",
    ),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download Model Comparison (CSV)",
    data=comparison_df.to_csv(index=False).encode("utf-8"),
    file_name="model_comparison_results.csv",
    mime="text/csv",
)

# ---------------------------------------------------------
# FORECAST CHART
# ---------------------------------------------------------
st.subheader("Forecast versus actual cases")

fig, ax = plt.subplots(figsize=(12, 5))

tail = min(
    len(train),
    12 if unit == "week" else 60,
)

ax.plot(
    train.index[-tail:],
    train.values[-tail:],
    label=f"Training history (last {tail} {unit}s)",
    color="gray",
)

ax.plot(
    test.index,
    test.values,
    label="Actual test observations",
    color="black",
    linewidth=2,
)

for label, (n, prediction) in prediction_columns.items():
    ax.plot(
        test.index[:n],
        prediction,
        linestyle="--",
        linewidth=1.6,
        label=label,
    )

ax.set_xlabel("Date")
ax.set_ylabel(f"New cases per {unit}")
ax.grid(True, alpha=0.25)
ax.legend(loc="best", fontsize=8)

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ---------------------------------------------------------
# METRIC GUIDE
# ---------------------------------------------------------
with st.expander("How to interpret the metrics"):
    st.markdown(
        """
        - **MAE:** Average absolute error in case counts.
        - **RMSE:** Penalizes large errors more heavily than MAE.
        - **R²:** Negative values mean the predictions performed worse
          than a constant-mean reference on this test set.
        - **Naive baseline:** Repeats the average of the last seven
          training observations.
        - **ARIMA:** Selects an order using AIC from the searched grid.
        - **LSTM:** Learns patterns in sequences; it may overfit and
          does not guarantee better forecasts.
        """
    )

# ---------------------------------------------------------
# EVALUATION LIMITATIONS
# ---------------------------------------------------------
with st.expander("Evaluation limitations and next steps"):
    st.markdown(
        """
        1. Use rolling-origin evaluation so every model is assessed
           on equivalent forecast dates and information.
        2. Compare against simple baselines before claiming an
           improvement.
        3. Report results across several forecast origins, not just
           one train/test split.
        4. Inspect reporting gaps, revisions, and missing data.
        5. Treat this project as a research prototype, not a tool
           for diagnosing or managing individual patients.
        """
    )

# ---------------------------------------------------------
# DOWNLOAD FORECAST RESULTS
# ---------------------------------------------------------
output = pd.DataFrame(
    {
        "date": test.index,
        "actual": actual,
    }
).set_index("date")

for label, (n, prediction) in prediction_columns.items():
    output[label] = np.nan
    output.loc[output.index[:n], label] = prediction

st.download_button(
    "Download forecast results (CSV)",
    data=output.to_csv().encode("utf-8"),
    file_name=(
        f"forecast_results_{dataset_key.split()[0].lower()}.csv"
    ),
    mime="text/csv",
)

st.caption(
    "AI-driven outbreak forecasting research prototype. "
    "Forecasts are experimental and should not be used for clinical decisions."
)
