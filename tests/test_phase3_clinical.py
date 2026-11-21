from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db

client = TestClient(app)


def test_get_medical_records():
    resp = client.get("/api/v1/medical-records?patientId=patient_01")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "summary" in data[0]


def test_get_prescriptions():
    resp = client.get("/api/v1/prescriptions?patientId=patient_01")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "items" in data[0]


def test_get_lab_tests_and_orders():
    # 1. Tests catalog
    resp_tests = client.get("/api/v1/lab/tests")
    assert resp_tests.status_code == 200
    assert len(resp_tests.json()) > 0

    # 2. Lab orders & reports
    resp_orders = client.get("/api/v1/lab/orders?patientId=patient_01")
    assert resp_orders.status_code == 200
    assert len(resp_orders.json()) > 0


def test_get_vitals():
    resp = client.get("/api/v1/vitals?patientId=patient_01")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "bloodPressure" in data[0]


def test_doctor_emergency_leave():
    mock_db = AsyncMock()
    mock_doc = MagicMock()
    mock_doc.id = "doc_01"
    mock_doc.name = "Dr. Sreelatha Menon"
    mock_doc.is_available_today = True

    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_doc
    mock_db.execute.return_value = mock_res
    mock_db.commit = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        # Apply emergency leave
        resp_leave = client.post(
            "/api/v1/doctors/doc_01/emergency-leave",
            json={"reason": "Urgent Surgery in Cath Lab"},
        )
        assert resp_leave.status_code == 200
        assert resp_leave.json()["success"] is True
        assert resp_leave.json()["availability"] == "On Emergency Leave"

        # Resume duty
        resp_resume = client.post("/api/v1/doctors/doc_01/resume-duty")
        assert resp_resume.status_code == 200
        assert resp_resume.json()["success"] is True
        assert resp_resume.json()["availability"] == "Available"
    finally:
        app.dependency_overrides.clear()
