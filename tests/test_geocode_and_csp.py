from fastapi.testclient import TestClient

from app.main import app
from app.routers import geocode

client = TestClient(app)


class MockGeoResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "results": [
                {
                    "name": "Delhi",
                    "latitude": 28.65195,
                    "longitude": 77.23149,
                    "country": "India",
                    "admin1": "National Capital Territory of Delhi",
                }
            ]
        }


def test_geocode_proxy(monkeypatch):
    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, *args, **kwargs):
            return MockGeoResponse()

    monkeypatch.setattr(geocode.httpx, "AsyncClient", lambda timeout: MockClient())
    response = client.get("/api/geocode?name=Delhi")
    assert response.status_code == 200
    assert response.json()["results"][0]["latitude"] == 28.65195


def test_geocode_api_empty_result(monkeypatch):
    class EmptyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"results": []}

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, *args, **kwargs):
            return EmptyResponse()

    monkeypatch.setattr(geocode.httpx, "AsyncClient", lambda timeout: MockClient())
    response = client.get("/api/geocode?name=NoSuchCity")
    assert response.status_code == 200
    assert response.json() == {"results": []}


def test_geocode_rejects_short_name():
    response = client.get("/api/geocode?name=x")
    assert response.status_code == 422


def test_csp_and_favicon():
    response = client.get("/")
    csp = response.headers["content-security-policy"]
    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp
    assert "connect-src 'self'" in csp
    favicon = client.get("/favicon.ico")
    assert favicon.status_code == 200
    assert favicon.headers["content-type"].startswith("image/svg+xml")
