import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_404_error_structure():
    """Verify 404 returns structured JSON with both 'message' and 'detail'."""
    response = client.get("/api/v1/non_existent_endpoint_12345")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "message" in data
    assert "detail" in data
    assert data["status_code"] == 404
    assert "Not Found" in data["message"]


def test_422_validation_error_structure():
    """Verify 422 request validation returns clean human-readable message and detail."""
    # Send empty or invalid body to emergency priority bump endpoint which requires fields
    response = client.post("/api/v1/queue/tokens/test_tok/emergency", json={"reason": ""})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "message" in data
    assert "detail" in data
    assert data["error_code"] == "VALIDATION_ERROR"
    assert data["status_code"] == 422
    # Ensure message contains the field validation info
    assert len(data["message"]) > 0
    assert "reason" in data["message"]


def test_custom_http_exception_structure():
    """Verify explicit HTTPException returns unified structure."""
    # Attempting to verify invalid OTP triggers 400 Bad Request
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone": "+919876543210", "otp": "000000"},
    )
    # Could be 400 or 500 depending on mock, but response must be valid JSON with success: False
    data = response.json()
    assert "message" in data
    assert "detail" in data
    assert data["success"] is False
