from http import HTTPStatus

from app.src.health.router import HealthCheckResponse


def test_health_check(test_client):
    response = test_client.get("/api/v1/health/check")
    assert response.status_code == HTTPStatus.OK
    assert HealthCheckResponse(response.text) == HealthCheckResponse.OK


def test_health_ping(test_client):
    response = test_client.get("/api/v1/health/ping")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"ping": "pong!"}