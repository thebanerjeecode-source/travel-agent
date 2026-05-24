from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

JAPAN_REQUEST = (
    "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. "
    "Love food and temples, hate crowds."
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealth:
    def test_health(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestPlansAPI:
    def test_create_plan_dry_run(self, client: TestClient):
        response = client.post(
            "/api/v1/plans",
            json={"request": JAPAN_REQUEST, "dry_run": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert data["session_id"]
        assert len(data["trace"]) >= 7
        assert len(data["trip_plan"]["day_by_day"]) == 5
        assert data["trip_plan"]["validation_passed"] is True

    def test_get_plan_by_session_id(self, client: TestClient):
        created = client.post(
            "/api/v1/plans",
            json={"request": JAPAN_REQUEST, "dry_run": True},
        ).json()
        session_id = created["session_id"]

        fetched = client.get(f"/api/v1/plans/{session_id}")
        assert fetched.status_code == 200
        assert fetched.json()["session_id"] == session_id

    def test_markdown_export(self, client: TestClient):
        created = client.post(
            "/api/v1/plans",
            json={"request": JAPAN_REQUEST, "dry_run": True},
        ).json()
        session_id = created["session_id"]

        response = client.get(f"/api/v1/plans/{session_id}/markdown")
        assert response.status_code == 200
        assert "DAY-BY-DAY" in response.text or "Day 1" in response.text

    def test_empty_request_fails(self, client: TestClient):
        response = client.post(
            "/api/v1/plans",
            json={"request": "   ", "dry_run": True},
        )
        assert response.status_code == 422

    def test_plan_not_found(self, client: TestClient):
        response = client.get("/api/v1/plans/nonexistent-id")
        assert response.status_code == 404
