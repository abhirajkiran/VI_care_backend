from datetime import date
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.models.patient import Patient

client = TestClient(app)


def test_google_login():
    mock_db = AsyncMock()
    mock_patient = Patient(
        id="patient_01",
        uhid="PT-10001",
        name="Aravind Krishnan",
        email="aravind.krishnan@gmail.com",
        phone="+91 98765 43210",
        gender="Male",
        blood_group="O+",
    )

    res = MagicMock()
    res.scalar_one_or_none.return_value = mock_patient
    mock_db.execute.return_value = res

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.post("/api/v1/auth/google")
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "aravind.krishnan@gmail.com"
    finally:
        app.dependency_overrides.clear()


def test_patient_crud_mocked():
    mock_db = AsyncMock()
    real_patient = Patient(
        id="pat_test",
        uhid="PT-9999",
        name="Test Patient",
        phone="+91 99999 88888",
        email="test@patient.com",
        gender="Male",
        blood_group="B+",
        address="123 Street",
        date_of_birth=date(1995, 1, 1),
    )

    res = MagicMock()
    res.scalar_one_or_none.return_value = real_patient
    mock_db.execute.return_value = res
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.delete = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        # Create
        resp_create = client.post(
            "/api/v1/patients",
            json={"name": "Test Patient", "phone": "+91 99999 88888"},
        )
        assert resp_create.status_code == 200
        assert resp_create.json()["name"] == "Test Patient"

        # Update
        resp_update = client.patch(
            "/api/v1/patients/pat_test",
            json={"address": "New Address"},
        )
        assert resp_update.status_code == 200
        assert resp_update.json()["address"] == "New Address"

        # Delete
        resp_delete = client.delete("/api/v1/patients/pat_test")
        assert resp_delete.status_code == 200
        assert resp_delete.json()["success"] is True
    finally:
        app.dependency_overrides.clear()


def test_billing_and_payments():
    # 1. Get invoices
    resp_inv = client.get("/api/v1/billing/invoices?patientId=patient_01")
    assert resp_inv.status_code == 200
    data = resp_inv.json()
    assert isinstance(data, list)
    assert len(data) > 0
    inv_id = data[0]["id"]

    # 2. Pay bill
    resp_pay = client.post(
        "/api/v1/billing/pay",
        json={"billId": inv_id, "amount": 200.0, "paymentMethod": "UPI"},
    )
    assert resp_pay.status_code == 200
    assert resp_pay.json()["success"] is True
    assert "transactionId" in resp_pay.json()


def test_pharmacy_inventory_and_prescriptions():
    # 1. Inventory
    resp_meds = client.get("/api/v1/pharmacy/inventory")
    assert resp_meds.status_code == 200
    data = resp_meds.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "stockQuantity" in data[0]

    # 2. Prescriptions
    resp_rx = client.get("/api/v1/pharmacy/prescriptions?patientId=patient_01")
    assert resp_rx.status_code == 200
    assert isinstance(resp_rx.json(), list)
