from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_and_get_itinerary():
    payload = {
        "title": "Bali 2 days",
        "days": [
            {"day_number": 1, "stops": [{"place_id": 1, "order": 1}, {"place_id": 2, "order": 2}]},
            {"day_number": 2, "stops": [{"place_id": 3, "order": 1}]},
        ],
    }

    r = client.post("/itineraries", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Bali 2 days"
    assert len(data["days"]) == 2

    it_id = data["id"]
    r2 = client.get(f"/itineraries/{it_id}")
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["id"] == it_id


def test_create_itinerary_rejects_duplicate_day_number():
    payload = {
        "title": "Bad itinerary",
        "days": [
            {"day_number": 1, "stops": []},
            {"day_number": 1, "stops": []},
        ],
    }
    r = client.post("/itineraries", json=payload)
    assert r.status_code == 422  # validation error


def test_create_itinerary_rejects_unknown_place_id():
    payload = {
        "title": "Unknown place",
        "days": [{"day_number": 1, "stops": [{"place_id": 9999, "order": 1}]}],
    }
    r = client.post("/itineraries", json=payload)
    assert r.status_code == 400
