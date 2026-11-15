"""REST API that exposes health, the latest reading, and saved alerts."""

from fastapi import FastAPI  # The web framework that defines the endpoints

import db  # Our database module from db.py

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