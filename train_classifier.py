"""Train a Random Forest to recognise idle, cpu, memory and disk, then test it on unseen runs."""

import joblib                                     # Saves and loads the trained model
import pandas as pd                               # Table library, used to rank features
from sklearn.ensemble import RandomForestClassifier  # The model
from sklearn.metrics import (accuracy_score,      # Overall share of correct answers
                             classification_report,  # Precision, recall and F1 per class
                             confusion_matrix)       # 4 by 4 table of right and wrong answers

import db                                         # Database connection
from features import build_dataset                # Builds the feature table

MODEL_PATH = "model.joblib"                       # File where the trained model is saved
TRAIN_RUNS = 7                                    # Runs 1 to 7 of each class are for training
LABELS = ["cpu", "disk", "idle", "memory"]        # The four classes, in a fixed order
NON_FEATURE_COLUMNS = {"id", "run_id", "label", "ts"}  # Columns that are not model inputs


def run_number(run_id):
    # Turns "cpu-03-1794750000" into the number 3
    return int(run_id.split("-")[1])


def split_by_run(data):
    # Rows from runs 1 to 7 go to training; rows from runs 8 to 10 go to testing
    is_train = data["run_id"].map(run_number) <= TRAIN_RUNS
    return data[is_train], data[~is_train]


def feature_columns(data):
    # The list of numeric columns the model learns from
    return [c for c in data.columns if c not in NON_FEATURE_COLUMNS]


def main():
    conn = db.connect()                  # Opens metrics.db
    data = build_dataset(conn)           # Builds features for all 40 runs
    conn.close()

    train, test = split_by_run(data)     # Split by run number
    cols = feature_columns(data)         # Input columns

    # Create the forest: 100 trees, with a fixed seed so results repeat
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(train[cols], train["label"])  # Learn from training rows and their labels

    y_test = test["label"]               # The true answers for the test rows
    pred = model.predict(test[cols])     # The model's answers for the test rows

    print(f"Training rows: {len(train)}   Test rows: {len(test)}")
    print(f"Accuracy: {accuracy_score(y_test, pred):.3f}   (chance level with 4 equal classes: 0.25)")
    print()
    print(classification_report(y_test, pred, labels=LABELS, digits=3, zero_division=0))
    print(f"Confusion matrix. Rows = actual, columns = predicted, order = {LABELS}")
    print(confusion_matrix(y_test, pred, labels=LABELS))
    print()

    # Show which columns the model relied on most
    importances = pd.Series(model.feature_importances_, index=cols).sort_values(ascending=False)
    print("Top 10 features:")
    print(importances.head(10).round(3))

    # Save the model and its column list, so the API uses the same inputs in the same order
    joblib.dump({"model": model, "columns": cols}, MODEL_PATH)
    print(f"\nSaved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()