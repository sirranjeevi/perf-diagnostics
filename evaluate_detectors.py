"""Compare an Isolation Forest with a fixed CPU threshold, using run-level train/test splits."""

from sklearn.ensemble import IsolationForest                       # The anomaly model
from sklearn.metrics import (confusion_matrix, f1_score,           # Scoring functions
                             precision_score, recall_score)

import db                       # Database connection
from features import build_dataset  # Builds the feature table from features.py

CPU_THRESHOLD = 50     # Baseline rule: flag a row when CPU is above this percent
TRAIN_IDLE_RUNS = 7    # Idle runs 01 to 07 are for training; idle 08 to 10 are for testing

# Columns that are not model inputs: the id, run name, label and timestamp
NON_FEATURE_COLUMNS = {"id", "run_id", "label", "ts"}


def run_number(run_id):
    # Turns a run name like "cpu-03-1794750000" into the number 3
    return int(run_id.split("-")[1])


def split_by_run(data):
    # Training rows: idle runs with numbers 1 to 7. Every other row goes to testing.
    is_train = (data["label"] == "idle") & (data["run_id"].map(run_number) <= TRAIN_IDLE_RUNS)
    return data[is_train], data[~is_train]


def feature_columns(data):
    # Keeps only the numeric feature columns the model should learn from
    return [c for c in data.columns if c not in NON_FEATURE_COLUMNS]


def print_scores(y_true, y_pred, name):
    # Prints precision, recall, F1 and the confusion matrix for one detector
    print(f"\n{name}")
    print(f"  precision: {precision_score(y_true, y_pred, zero_division=0):.3f}")
    print(f"  recall:    {recall_score(y_true, y_pred, zero_division=0):.3f}")
    print(f"  F1:        {f1_score(y_true, y_pred, zero_division=0):.3f}")
    print("  confusion matrix, rows = actual (normal, anomaly), columns = predicted:")
    print(confusion_matrix(y_true, y_pred, labels=[0, 1]))


def main():
    conn = db.connect()                  # Opens metrics.db
    data = build_dataset(conn)           # Builds features for all 40 runs
    conn.close()

    train, test = split_by_run(data)     # Splits by run, not by row
    cols = feature_columns(data)         # The list of input columns

    # Train the Isolation Forest on normal (idle) rows only
    model = IsolationForest(n_estimators=100, random_state=42)  # 100 trees; fixed seed so results repeat
    model.fit(train[cols])

    # Ground truth: 1 = anomaly (any non-idle row), 0 = normal (idle row)
    y_true = (test["label"] != "idle").astype(int)

    # The model returns -1 for anomaly and 1 for normal; convert to 1 and 0
    y_iforest = (model.predict(test[cols]) == -1).astype(int)

    # Baseline: flag a row when its CPU value is above the fixed threshold
    y_baseline = (test["cpu_percent"] > CPU_THRESHOLD).astype(int)

    print(f"Training rows (idle runs 1-{TRAIN_IDLE_RUNS}): {len(train)}")
    print(f"Test rows: {len(test)}  (anomalies: {int(y_true.sum())}, normal: {int((y_true == 0).sum())})")

    print_scores(y_true, y_iforest, "Isolation Forest")
    print_scores(y_true, y_baseline, f"Fixed threshold (CPU > {CPU_THRESHOLD}%)")


if __name__ == "__main__":
    main()