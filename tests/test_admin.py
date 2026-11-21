from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_staff_list():
    resp = client.get("/api/v1/staff")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "role" in data[0]


def test_get_audit_logs():
    resp = client.get("/api/v1/audit-logs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "action" in data[0]
