"""Turn raw samples into features with Pandas, and build one labeled table from all runs."""

import pandas as pd  # Table library

import db            # Database connection from db.py

WINDOW = 5           # Number of readings in each rolling window (5 seconds)
METRICS = ["cpu_percent", "ram_percent", "disk_read_bps",
           "disk_write_bps", "net_recv_bps", "net_sent_bps"]  # Columns we build features for


def load_run(conn, run_id):
    # Read every row of one run into a DataFrame, in time order
    return pd.read_sql_query(
        "SELECT * FROM samples WHERE run_id = ? ORDER BY ts",
        conn,
        params=(run_id,),  # The ? is replaced by run_id, safely
    )


def add_features(df, window=WINDOW):
    # Add rolling features for each metric, then drop rows without a full window
    out = df.copy()  # Work on a copy so the original table is unchanged
    for col in METRICS:
        roll = out[col].rolling(window)          # Looks at the last `window` values at each row
        out[f"{col}_mean"] = roll.mean()         # Average of the window
        out[f"{col}_max"] = roll.max()           # Highest value in the window
        out[f"{col}_std"] = roll.std()           # How much the values vary in the window
        out[f"{col}_delta"] = out[col].diff()    # Change since the previous second
    return out.dropna()                          # The first few rows lack a full window, so remove them


def build_dataset(conn):
    # Build features for every run, then stack them into one table
    run_ids = [row[0] for row in conn.execute("SELECT DISTINCT run_id FROM samples").fetchall()]
    frames = []
    for run_id in run_ids:
        frames.append(add_features(load_run(conn, run_id)))  # Each run is processed on its own
    return pd.concat(frames, ignore_index=True)              # Stack all runs into one table


if __name__ == "__main__":
    conn = db.connect()
    data = build_dataset(conn)
    print("Runs per label:")
    print(data.groupby("label")["run_id"].nunique())  # Count of distinct runs for each label
    print("Table shape (rows, columns):", data.shape)  # Size of the feature table
    conn.close()