# ML-Assisted System Performance Diagnostics Platform

A Python project that records CPU, RAM, disk and network readings every second, stores them in SQLite, raises CPU alerts, classifies the type of workload, and shows the results through a REST API and a web dashboard.

## What it does

- **Collector** (`collector.py`): records readings every second and raises an alert when CPU stays above 80% for 10 seconds in a row. Each alert records the top processes at that moment.
- **Fault injection** (`fault_inject.py`, `workloads.py`): runs four known workloads (idle, cpu, memory, disk), 10 times each, 20 seconds per run, to create labelled data.
- **Features** (`features.py`): uses Pandas to add rolling-window features (mean, max, std, change) per run.
- **Anomaly detection** (`evaluate_detectors.py`): compares an Isolation Forest, trained on idle data only, with a fixed CPU threshold.
- **Workload classifier** (`train_classifier.py`): a Random Forest trained on runs 1 to 7 of each workload and tested on runs 8 to 10.
- **API** (`api.py`): `/health`, `/metrics`, `/alerts`, `/analyze?run_id=...` and `/dashboard`.
- **Dashboard** (`dashboard.py`): Plotly charts for one run plus a table of saved alerts.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install psutil fastapi uvicorn pandas numpy scikit-learn joblib plotly pytest httpx
```

## Running it

```powershell
python collector.py cpu          # Record live readings with a label (Ctrl+C to stop)
python fault_inject.py           # Create the labelled dataset (about 15 minutes)
python evaluate_detectors.py     # Isolation Forest vs fixed threshold
python train_classifier.py       # Random Forest; saves model.joblib
uvicorn api:app --reload         # Start the API
python -m pytest -v              # Run the tests
```

Open http://127.0.0.1:8000/dashboard in a browser for the dashboard.

## Results (measured on one laptop)

**Isolation Forest vs fixed CPU threshold** (test set: 528 seconds, 480 unusual, 48 normal)

| Method | Precision | Recall | F1 |
|---|---|---|---|
| Isolation Forest | 0.980 | 0.498 | 0.660 |
| Fixed rule (CPU > 50%) | 1.000 | 0.510 | 0.676 |

The Isolation Forest did not beat the simple rule. Caught share by workload: disk 99%, memory 31%, cpu 19%.

**Random Forest workload classifier** (test set: runs 8 to 10 of each workload, 192 seconds)

- Accuracy: 0.974 (chance level 0.25)
- cpu, idle: all seconds correct
- memory: recall 1.000, precision 0.906
- disk: recall 0.896 (5 of 48 seconds labelled memory)

## Limitations

- All data comes from one laptop and four synthetic workloads. Real programs will look different.
- Each workload has only 3 test runs, so one bad run changes the scores noticeably.
- The Isolation Forest test set is 91% unusual seconds, which flatters both methods. A test with mostly normal seconds would be fairer.
- The classifier only recognises the four workloads it was trained on.
- Alerts suggest where to look. They do not identify a root cause.
- Each alert pauses the collector for about one second to measure processes, so one sample is skipped.