from datetime import date
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db

client = TestClient(app)


def test_queue_pause_and_resume():
    # 1. Pause queue
    resp_pause = client.post(
        "/api/v1/queue/session/pause",
        json={"doctorId": "doc_01", "hospitalId": "hosp_01", "reason": "Tea Break"},
    )
    assert resp_pause.status_code == 200
    assert resp_pause.json()["success"] is True
    assert resp_pause.json()["session"]["isPaused"] is True

    # 2. Set delay
    resp_delay = client.post(
        "/api/v1/queue/session/delay",
        json={"doctorId": "doc_01", "hospitalId": "hosp_01", "delayMinutes": 20},
    )
    assert resp_delay.status_code == 200
    assert resp_delay.json()["session"]["delayMinutes"] == 20

    # 3. Resume queue
    resp_resume = client.post(
        "/api/v1/queue/session/resume",
        json={"doctorId": "doc_01", "hospitalId": "hosp_01"},
    )
    assert resp_resume.status_code == 200
    assert resp_resume.json()["session"]["isPaused"] is False


def test_queue_summary_mocked():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get("/api/v1/queue/summary?doctorId=doc_01&hospitalId=hosp_01")
        assert resp.status_code == 200
        data = resp.json()
        assert "tokens" in data
        assert "waitingCount" in data
    finally:
        app.dependency_overrides.clear()


def test_queue_emergency_validation():
    # Emergency without reason should fail validation (min_length=3)
    resp = client.post("/api/v1/queue/tokens/test_tok/emergency", json={"reason": ""})
    assert resp.status_code == 422


def test_queue_start_consultation_mocked():
    mock_db = AsyncMock()
    mock_appt = MagicMock()
    mock_appt.id = "APT-1001"
    mock_appt.token_number = "A-01"
    mock_appt.doctor_id = "doc_01"
    mock_appt.hospital_id = "hosp_01"
    mock_appt.appointment_date = date.today()
    mock_appt.status = "checkedIn"

    # Mock finding appointment and no other active consultation
    res1 = MagicMock()
    res1.scalar_one_or_none.return_value = mock_appt
    res2 = MagicMock()
    res2.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [res1, res2]
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post("/api/v1/queue/tokens/APT-1001/start")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["status"] == "In Consultation"
    finally:
        app.dependency_overrides.clear()
