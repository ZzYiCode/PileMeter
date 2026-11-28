from fastapi.testclient import TestClient

from pile_meter.interfaces.api.main import app


def test_health_endpoint_reports_scaffold_capabilities() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["scale_status"] == "relative"
    assert payload["capabilities"]["vggt_reconstruction"] is True
    assert payload["capabilities"]["pointcloud_viewer"] is True
