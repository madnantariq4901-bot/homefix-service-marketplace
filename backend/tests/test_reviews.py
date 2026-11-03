# tests/test_reviews.py
from tests.test_jobs import _make_provider_ready, _set_provider_available, _verify_provider


def test_review_appears_in_provider_review_list(client, customer, provider, category, db_session):
    p_headers, p_user = _make_provider_ready(client, provider, category)
    _verify_provider(db_session, p_user["id"])
    _set_provider_available(client, p_headers)

    c_headers, _ = customer
    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Fix plumbing", "address": "Test address", "lat": 31.52, "lng": 74.35},
        headers=c_headers,
    ).json()
    job_id = job["id"]

    client.post(f"/jobs/{job_id}/quote", json={"quoted_amount": 50.0}, headers=p_headers)
    quotes = client.get(f"/jobs/{job_id}/quotes", headers=c_headers).json()
    client.post(f"/jobs/{job_id}/quotes/{quotes[0]['id']}/accept", headers=c_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "en_route"}, headers=p_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "in_progress"}, headers=p_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "completed", "final_amount": 60.0}, headers=p_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "completed"}, headers=c_headers)
    client.post(f"/jobs/{job_id}/review", json={"rating": 4, "comment": "Good"}, headers=c_headers)

    profile = client.get("/providers/me", headers=p_headers).json()
    resp = client.get(f"/providers/{profile['id']}/reviews")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["rating"] == 4