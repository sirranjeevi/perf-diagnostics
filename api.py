"""REST API that exposes health, the latest reading, and saved alerts."""

from fastapi import FastAPI  # The web framework that defines the endpoints

import db  # Our database module from db.py
from fastapi.responses import HTMLResponse   # Tells the browser the reply is a web page, not plain text
import dashboard                             # Builds the dashboard page from dashboard.py

app = FastAPI(title="Performance Diagnostics API")  # Creates the application object


@app.get("/health")  # Runs this function when someone requests /health
def health():
    # Returns a fixed status. If this responds, the service is running.
    return {"status": "ok"}


@app.get("/metrics")  # Runs this function when someone requests /metrics
def latest_metrics():
    # Open the database, read the newest sample, then close it
    conn = db.connect()
    try:
        row = conn.execute(
            """
            SELECT run_id, label, ts, cpu_percent, ram_percent
            FROM samples
            ORDER BY ts DESC   -- newest first
            LIMIT 1            -- keep only one row
            """
        ).fetchone()           # Returns None if the table is empty
    finally:
        conn.close()           # Always close the file, even if the query fails

    if row is None:
        return None            # No readings saved yet; JSON null

    run_id, label, ts, cpu, ram = row
    return {
        "run_id": run_id,
        "label": label,
        "ts": ts,
        "cpu_percent": cpu,
        "ram_percent": ram,
    }


@app.get("/alerts")  # Runs this function when someone requests /alerts
def list_alerts():
    conn = db.connect()
    try:
        rows = conn.execute(
            """
            SELECT run_id, ts, metric, value, threshold, seconds, message, top_processes
            FROM alerts
            ORDER BY ts DESC   -- newest first
            LIMIT 50           -- at most 50 alerts per response
            """
        ).fetchall()           # Returns a list of tuples, one per row
    finally:
        conn.close()

    # Names for each position in the tuple, so the JSON has labelled fields
    keys = ["run_id", "ts", "metric", "value", "threshold", "seconds", "message", "top_processes"]
    return [dict(zip(keys, row)) for row in rows]  # Turns each tuple into a dictionary

@app.get("/analyze")  # Requests look like: /analyze?run_id=cpu-01-1794839838
def analyze(run_id: str):
    # Load the trained model. If it doesn't exist yet, tell the caller clearly.
    try:
        saved = joblib.load("model.joblib")
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model not trained yet. Run train_classifier.py first.")

    # Read the requested run from the database
    conn = db.connect()
    try:
        df = load_run(conn, run_id)
    finally:
        conn.close()

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No run named {run_id}")

    # Build the same rolling features the model was trained on
    feats = add_features(df)
    if feats.empty:
        raise HTTPException(status_code=400, detail="Run is too short: it needs at least 5 readings")

    # Predict one label per second, using the columns in the same order as training
    preds = saved["model"].predict(feats[saved["columns"]])
    counts = Counter(str(p) for p in preds)     # How many seconds got each label

    # The workload is the label that appeared most often
    best_label, _ = counts.most_common(1)[0]

    return {
        "run_id": run_id,
        "predicted_workload": best_label,
        "seconds_per_label": dict(counts),
    }

@app.get("/dashboard", response_class=HTMLResponse)  # Open http://127.0.0.1:8000/dashboard in a browser
def dashboard_page(run_id: str | None = None):
    # run_id is optional: without it, the newest run is shown
    conn = db.connect()
    try:
        return dashboard.build_page(conn, run_id)  # Returns the full HTML page
    finally:
        conn.close()  # Always close the database file