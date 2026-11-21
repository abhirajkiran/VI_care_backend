from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db

client = TestClient(app)


def test_get_all_hospitals():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get("/api/v1/hospitals")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
    finally:
        app.dependency_overrides.clear()


def test_get_departments():
    resp = client.get("/api/v1/departments")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]


def test_get_department_names():
    resp = client.get("/api/v1/departments/names")
    assert resp.status_code == 200
    data = resp.json()
    assert "Cardiology" in data
    assert "All" in data
