from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.core.security import get_current_user_id

client = TestClient(app)


def test_get_appointments_mocked():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user_id] = lambda: "patient_01"

    try:
        resp = client.get("/api/v1/appointments")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    finally:
        app.dependency_overrides.clear()
