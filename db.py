"""SQLite storage for telemetry samples and alerts."""

import sqlite3

DB_PATH = "metrics.db"  # The database file, created in the project folder

# Table for one row per second of readings
SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    label TEXT NOT NULL,
    ts REAL NOT NULL,
    cpu_percent REAL NOT NULL,
    ram_percent REAL NOT NULL,
    disk_read_bps REAL NOT NULL,
    disk_write_bps REAL NOT NULL,
    net_recv_bps REAL NOT NULL,
    net_sent_bps REAL NOT NULL
)
"""

# Table for alerts. One row each time a sustained-threshold rule fires.
ALERTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    ts REAL NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    threshold REAL NOT NULL,
    seconds INTEGER NOT NULL,
    message TEXT NOT NULL,
    top_processes TEXT NOT NULL
)
"""


def connect(path=DB_PATH):
    """Open the database file and create both tables if they don't exist yet."""
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)         # Creates the samples table if missing
    conn.execute(ALERTS_SCHEMA)  # Creates the alerts table if missing
    conn.commit()
    return conn


def insert_sample(conn, run_id, label, ts, cpu, ram, disk_r, disk_w, net_rx, net_tx):
    """Save one row of readings into the samples table."""
    conn.execute(
        """
        INSERT INTO samples
            (run_id, label, ts, cpu_percent, ram_percent,
             disk_read_bps, disk_write_bps, net_recv_bps, net_sent_bps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, label, ts, cpu, ram, disk_r, disk_w, net_rx, net_tx),
    )
    conn.commit()


def insert_alert(conn, run_id, ts, metric, value, threshold, seconds, message, top_processes):
    """Save one alert into the alerts table."""
    conn.execute(
        """
        INSERT INTO alerts
            (run_id, ts, metric, value, threshold, seconds, message, top_processes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_id, ts, metric, value, threshold, seconds, message, top_processes),
    )
    conn.commit()