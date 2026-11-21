import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db

client = TestClient(app)


def test_auth_send_otp():
    # 1. Send OTP
    resp_otp = client.post("/api/v1/auth/send-otp", json={"phone": "+919876543210"})
    assert resp_otp.status_code == 200
    otp_data = resp_otp.json()
    assert otp_data.get("success") is True
    assert "otp_demo" in otp_data


def test_auth_verify_otp():
    # Mock DB session dependency so unit test runs fast and independent of DB state
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        resp_verify = client.post(
            "/api/v1/auth/verify-otp",
            json={"phone": "+919876543210", "otp": "123456"},
        )
        assert resp_verify.status_code == 200
        data = resp_verify.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    finally:
        app.dependency_overrides.clear()

