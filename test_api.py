"""Automated tests for the API endpoints."""

from fastapi.testclient import TestClient  # Calls the app directly, without starting a server

from api import app  # The application object defined in api.py

client = TestClient(app)  # One client we reuse in every test


def test_health_returns_ok():
    # Ask for /health and check the status code and the body
    response = client.get("/health")
    assert response.status_code == 200          # 200 means success
    assert response.json() == {"status": "ok"}  # The body must match exactly


def test_metrics_has_expected_fields():
    # /metrics returns null when no readings exist, so only check the shape when data is present
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    if data is not None:
        assert set(data) == {"run_id", "label", "ts", "cpu_percent", "ram_percent"}


def test_alerts_returns_a_list():
    # /alerts always returns a list, even when it's empty
    response = client.get("/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)