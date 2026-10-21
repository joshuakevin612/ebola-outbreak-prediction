"""Small JSON API for the React interface; reuses the research project models."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import traceback
from urllib.parse import parse_qs, urlparse

import numpy as np

from forecasting import (
    DATASETS,
    TENSORFLOW_AVAILABLE,
    adf_test,
    chronological_split,
    evaluate,
    fit_arima,
    fit_lstm,
    fit_lstm_pooled,
    load_series,
    naive_forecast,
)
from src1.predict import load_model, predict_risk


ROOT = Path(__file__).resolve().parent
MODEL = load_model()


def to_json_value(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.ndarray):
        return [to_json_value(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {key: to_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_value(item) for item in value]
    return value


def series_payload(dataset_key):
    series = load_series(dataset_key, data_dir=str(ROOT))
    return {
        "dataset": dataset_key,
        "frequency": "day" if DATASETS[dataset_key]["freq"] == "D" else "week",
        "observations": len(series),
        "start": series.index.min().date().isoformat(),
        "end": series.index.max().date().isoformat(),
        "peak": float(series.max()),
        "dates": [date.date().isoformat() for date in series.index],
        "cases": series.to_numpy(dtype=float).tolist(),
        "adf": to_json_value(adf_test(series)),
    }


class ApiHandler(BaseHTTPRequestHandler):
    def log_message(self, _format, *_args):
        return

    def send_json(self, status, payload):
        body = json.dumps(to_json_value(payload)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_json(200, {"ok": True})

    def do_GET(self):
        try:
            if self.path == "/api/status":
                return self.send_json(200, {
                    "ok": True,
                    "tensorflow": TENSORFLOW_AVAILABLE,
                    "datasets": list(DATASETS),
                })
            if self.path.startswith("/api/series"):
                from urllib.parse import parse_qs, urlparse
                query = parse_qs(urlparse(self.path).query)
                key = query.get("dataset", [next(iter(DATASETS))])[0]
                if key not in DATASETS:
                    return self.send_json(400, {"error": "Choose a listed outbreak dataset."})
                return self.send_json(200, series_payload(key))
            return self.send_json(404, {"error": "That API route does not exist."})
        except Exception as exc:
            return self.send_json(500, {"error": str(exc)})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/risk":
                score = predict_risk(MODEL, body["patient"])
                return self.send_json(200, {"score": float(score)})
            if self.path == "/api/forecast":
                return self.send_json(200, self.run_forecast(body))
            return self.send_json(404, {"error": "That API route does not exist."})
        except Exception as exc:
            traceback.print_exc()
            return self.send_json(400, {"error": str(exc)})

    def run_forecast(self, body):
        dataset_key = body.get("dataset", next(iter(DATASETS)))
        if dataset_key not in DATASETS:
            raise ValueError("Choose a listed outbreak dataset.")
        test_frac = float(body.get("testFrac", 0.2))
        if not 0.1 <= test_frac <= 0.4:
            raise ValueError("Test proportion must be between 10% and 40%.")

        selected = body.get("models", ["naive", "arima"])
        series = load_series(dataset_key, data_dir=str(ROOT)).sort_index()
        train, test = chronological_split(series, test_frac)
        if len(train) < 10 or len(test) < 1:
            raise ValueError("This split leaves too few observations to evaluate.")

        predictions = {}
        errors = {}
        if "naive" in selected:
            predictions["Naive (7-point average)"] = naive_forecast(
                train, len(test), method="moving_avg"
            )
        if "arima" in selected:
            result = fit_arima(
                train, len(test), max_p=int(body.get("maxP", 3)),
                max_q=int(body.get("maxP", 3))
            )
            predictions[f"ARIMA {result['order']}"] = np.asarray(result["forecast"], dtype=float).ravel()
        if "lstm" in selected and TENSORFLOW_AVAILABLE:
            predictions["LSTM (single-series)"] = fit_lstm(
                series, len(train), int(body.get("lookback", DATASETS[dataset_key]["lookback"])),
                epochs=int(body.get("epochs", 100))
            )[0]
        if "pooled" in selected and TENSORFLOW_AVAILABLE:
            all_series = {key: load_series(key, data_dir=str(ROOT)) for key in DATASETS}
            train_by_name, test_by_name = {}, {}
            for key, current in all_series.items():
                train_by_name[key], test_by_name[key] = chronological_split(current, test_frac)
            pooled, _ = fit_lstm_pooled(
                train_by_name, test_by_name,
                lookback=min(DATASETS[key]["lookback"] for key in DATASETS),
                epochs=int(body.get("epochs", 100)),
            )
            predictions["LSTM (pooled)"] = pooled[dataset_key]
        if not predictions:
            raise ValueError("Select at least one available model.")

        actual = test.to_numpy(dtype=float)
        metrics, output_predictions = [], {}
        for name, prediction in predictions.items():
            prediction = np.asarray(prediction, dtype=float).ravel()
            count = min(len(actual), len(prediction))
            try:
                score = evaluate(actual[:count], prediction[:count])
                metrics.append({"model": name, "rmse": score["rmse"], "mae": score["mae"], "r2": score["r2"]})
                output_predictions[name] = [*prediction[:count].tolist(), *([None] * (len(actual) - count))]
            except Exception as exc:
                errors[name] = str(exc)
        return {
            "dataset": dataset_key,
            "frequency": "day" if DATASETS[dataset_key]["freq"] == "D" else "week",
            "trainingCount": len(train),
            "testCount": len(test),
            "testStart": test.index.min().date().isoformat(),
            "testEnd": test.index.max().date().isoformat(),
            "dates": [date.date().isoformat() for date in test.index],
            "historyDates": [date.date().isoformat() for date in train.index[-min(len(train), 60 if DATASETS[dataset_key]["freq"] == "D" else 12):]],
            "historyCases": train.to_numpy(dtype=float)[-min(len(train), 60 if DATASETS[dataset_key]["freq"] == "D" else 12):].tolist(),
            "actual": actual.tolist(),
            "predictions": output_predictions,
            "metrics": metrics,
            "errors": errors,
        }


def process_stdio_message(message):
    """Handle a JSON request over stdin/stdout for the Vite dev bridge."""
    try:
        method, url = message.get("method", "GET"), message.get("url", "/")
        body = message.get("body") or {}
        if method == "GET" and url == "/api/status":
            return 200, {"ok": True, "tensorflow": TENSORFLOW_AVAILABLE, "datasets": list(DATASETS)}
        if method == "GET" and url.startswith("/api/series"):
            query = parse_qs(urlparse(url).query)
            key = query.get("dataset", [next(iter(DATASETS))])[0]
            if key not in DATASETS:
                return 400, {"error": "Choose a listed outbreak dataset."}
            return 200, series_payload(key)
        if method == "POST" and url == "/api/risk":
            return 200, {"score": float(predict_risk(MODEL, body["patient"]))}
        if method == "POST" and url == "/api/forecast":
            handler = ApiHandler.__new__(ApiHandler)
            return 200, handler.run_forecast(body)
        return 404, {"error": "That API route does not exist."}
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        return 400, {"error": str(exc)}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        for line in sys.stdin:
            try:
                status, payload = process_stdio_message(json.loads(line))
                print(json.dumps({"status": status, "payload": to_json_value(payload)}), flush=True)
            except Exception as exc:
                print(json.dumps({"status": 500, "payload": {"error": str(exc)}}), flush=True)
        raise SystemExit(0)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), ApiHandler)
    print("EbolaVF API listening at http://127.0.0.1:8000")
    server.serve_forever()
