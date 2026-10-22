"""SQLite storage for telemetry samples."""

import sqlite3

DB_PATH = "metrics.db"

# One row per sample. run_id and label let us group readings from fault-injection runs later.
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


def connect(path=DB_PATH):
    """Open the database file and create the table if it doesn't exist yet."""
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def insert_sample(conn, run_id, label, ts, cpu, ram, disk_r, disk_w, net_rx, net_tx):
    """Save one row of readings."""
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