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

def _create_sample_itinerary():
    payload = {
        "title": "Bali CRUD",
        "days": [
            {"day_number": 1, "stops": [{"place_id": 1, "order": 1}, {"place_id": 2, "order": 2}]},
            {"day_number": 2, "stops": [{"place_id": 3, "order": 1}]},
        ],
    }
    r = client.post("/itineraries", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_put_replaces_itinerary():
    it_id = _create_sample_itinerary()

    new_payload = {
        "title": "Bali CRUD UPDATED",
        "days": [
            {"day_number": 1, "stops": [{"place_id": 1, "order": 1}]},
        ],
    }
    r = client.put(f"/itineraries/{it_id}", json=new_payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["title"] == "Bali CRUD UPDATED"
    assert len(data["days"]) == 1
    assert len(data["days"][0]["stops"]) == 1

    r2 = client.get(f"/itineraries/{it_id}")
    assert r2.status_code == 200
    assert r2.json()["title"] == "Bali CRUD UPDATED"


def test_patch_updates_title_only():
    it_id = _create_sample_itinerary()

    r = client.patch(f"/itineraries/{it_id}", json={"title": "Title patched"})
    assert r.status_code == 200, r.text
    assert r.json()["title"] == "Title patched"


def test_delete_itinerary():
    it_id = _create_sample_itinerary()

    r = client.delete(f"/itineraries/{it_id}")
    assert r.status_code == 204, r.text

    r2 = client.get(f"/itineraries/{it_id}")
    assert r2.status_code == 404
