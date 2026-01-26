from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_places_returns_data():
    r = client.get("/places")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "name" in data[0]


def test_filter_places_by_area():
    r = client.get("/places", params={"area": "Ubud"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert all(p["area"].lower() == "ubud" for p in data)


def test_get_place_by_id():
    r = client.get("/places/2")
    assert r.status_code == 200
    assert r.json()["id"] == 2


def test_get_place_not_found():
    r = client.get("/places/9999")
    assert r.status_code == 404
