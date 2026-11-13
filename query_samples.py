"""List recorded runs, or show the readings for one run."""

import sys
import time

import db  # Reuses connect() from db.py


def clock(ts):
    """Turn a timestamp number like 1729620000.5 into a clock time like 20:18:58."""
    return time.strftime("%H:%M:%S", time.localtime(ts))


def list_runs(conn):
    """Print one line per run: its label, how many rows it has, and when it started and ended."""
    rows = conn.execute(
        """
        SELECT run_id, label, COUNT(*), MIN(ts), MAX(ts)
        FROM samples
        GROUP BY run_id, label
        ORDER BY MIN(ts)
        """
    ).fetchall()
    for run_id, label, count, start, end in rows:
        print(f"{run_id}  label={label}  rows={count}  {clock(start)} -> {clock(end)}")


def show_run(conn, run_id):
    """Print every reading for one run, using a time-range query."""
    # First find when this run started and ended
    start, end = conn.execute(
        "SELECT MIN(ts), MAX(ts) FROM samples WHERE run_id = ?", (run_id,)
    ).fetchone()

    if start is None:
        print(f"No run named {run_id}")
        return

    # Then fetch the rows whose timestamp falls between those two values
    rows = conn.execute(
        """
        SELECT ts, cpu_percent, ram_percent
        FROM samples
        WHERE ts BETWEEN ? AND ?
        ORDER BY ts
        """,
        (start, end),
    ).fetchall()

    print(f"{'TIME':10}{'CPU %':>8}{'RAM %':>8}")
    for ts, cpu, ram in rows:
        print(f"{clock(ts):10}{cpu:8.1f}{ram:8.1f}")


def main():
    conn = db.connect()  # Opens metrics.db
    try:
        if len(sys.argv) > 1:
            show_run(conn, sys.argv[1])  # Use: python query_samples.py run-1792680537
        else:
            list_runs(conn)              # Use: python query_samples.py
    finally:
        conn.close()                     # Always close the file when finished


if __name__ == "__main__":
    main()