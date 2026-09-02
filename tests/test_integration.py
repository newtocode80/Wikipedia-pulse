from src.app import app


def test_echo_route():
    client = app.test_client()

    response = client.post(
        "/echo_user_input",
        data={"user_input": "Tony"}
    )

    assert response.status_code == 200
    assert response.data == b"You entered: Tony"


def test_health_endpoint():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "ok"
    assert data["service"] == "wikipedia-pulse"


def test_metrics_endpoint():
    client = app.test_client()

    response = client.get("/metrics")

    assert response.status_code == 200

    data = response.get_json()

    assert "requests_total" in data
    assert "requests_last_60_seconds" in data
    assert "requests_per_second" in data
    assert data["window_seconds"] == 60

    assert data["requests_total"] >= 1
    assert data["requests_per_second"] >= 0

def test_report_endpoint():
    client = app.test_client()

    response = client.get("/report")

    assert response.status_code == 200
    assert b"Wikipedia Pulse Report" in response.data