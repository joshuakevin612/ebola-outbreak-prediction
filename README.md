# EbolaVF: Ebola Risk and Forecasting Research Prototype

EbolaVF is a research prototype with two interactive workspaces: a patient risk score from a saved Random Forest pipeline, and historical Ebola case exploration with configurable forecasting. The React interface uses a small Python API; a Streamlit forecasting dashboard is also included.

> **Research use only.** Model outputs are experimental and are not a diagnosis, validated probability, or guidance for clinical or public-health decisions.

## What is included

- **Patient risk:** a saved scikit-learn Random Forest pipeline accepts patient symptoms, exposure history, profile, and vitals and returns a model score.
- **Outbreak forecasting:** inspect the West Africa (2014–2016) and DRC North Kivu / Ituri (2018–2020) series. The interface compares a moving-average baseline and ARIMA; single-series and pooled LSTM options are available when TensorFlow loads.
- **React app:** landing page, interactive filament illustration, theme toggle, patient risk intake, and forecast controls.
- **Streamlit app:** `app.py` provides a separate forecasting dashboard.
- **Training code:** `src1/train.py` trains and saves the patient risk pipeline from `data/ebola_10000_balanced.csv`.

## Requirements

- Python 3.10–3.12 (Python 3.11 is a suitable choice)
- Node.js 20 or newer and npm
- The supplied model and cleaned outbreak datasets, kept in `models/` and the repository root

TensorFlow is listed in `requirements.txt` for LSTM forecasts. Without TensorFlow, the API and the baseline and ARIMA forecasting options still work; LSTM options are omitted.

## Setup and run the React app

From the project root, create and activate a virtual environment, install Python packages, then install and start the frontend:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd frontend
npm ci
npm run dev
```

Open the local URL printed by Vite (normally `http://127.0.0.1:5173`). Vite starts `api.py` as a child process and forwards `/api` calls to it. Start the dev server from `frontend/`; its Vite configuration locates the API and model relative to the project root. If PowerShell blocks activation, use `\.venv\Scripts\python.exe -m pip ...` and `\.venv\Scripts\python.exe` in place of the activated `python` command.

## Run the API or Streamlit dashboard separately

From the project root, with the virtual environment active:

```powershell
python api.py
```

The standalone JSON API listens on `http://127.0.0.1:8000`. The development frontend starts this API automatically, so do not start a second copy on the same port.

To run the forecasting dashboard instead:

```powershell
python -m streamlit run app.py
```

## Train the patient model

Training overwrites `models/ebola_model.pkl`. Keep a copy of the current model if you need to preserve it.

```powershell
python src1/train.py
```

## Project layout

```text
api.py                  JSON API used by React
app.py                  Streamlit forecasting dashboard
forecasting.py          Shared case-series loading and forecasting logic
forecast_pipeline.py    Optional command-line model comparison pipeline
data/                   Patient training data
models/                 Saved patient risk model
pages/                  Additional Streamlit page
src1/                   Patient model preprocessing, training, and prediction
frontend/               Vite and React interface
*_ebola_*_clean.csv     Historical outbreak series used by forecasting
```

## Notes

- Forecasting evaluates chronological train/test splits; results depend on the chosen outbreak, split, model settings, and optional TensorFlow availability.
- The saved model was serialized with joblib. Use compatible scikit-learn and Python versions if loading fails after changing dependencies.
- When deploying the static frontend build, serve `frontend/dist` and route `/api` requests to a separately running Python API.
