from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_v1_router_exposes_core_domain_skeletons() -> None:
    client = TestClient(create_app())

    for path in [
        "/api/v1/companies",
        "/api/v1/workers",
        "/api/v1/hiring",
        "/api/v1/visas",
        "/api/v1/documents",
        "/api/v1/contacts",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json() == []
