from app.core.security import create_access_token
from app.database.models.job import Job
from app.database.models.provider import ProviderProfile


def test_job_chat_is_limited_to_customer_and_assigned_provider(client, customer, provider, make_user, category, db_session):
    customer_headers, customer_user = customer
    provider_headers, provider_user = provider
    outsider_headers, _ = make_user(email="chat-outsider@example.com", role="customer")

    job_response = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Fix the front door", "address": "8 Oak Road"},
        headers=customer_headers,
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]

    provider_profile = db_session.query(ProviderProfile).filter(ProviderProfile.user_id == provider_user["id"]).one()
    job = db_session.query(Job).filter(Job.id == job_id).one()
    job.provider_id = provider_profile.id
    db_session.commit()

    customer_token = customer_headers["Authorization"].removeprefix("Bearer ")
    provider_token = provider_headers["Authorization"].removeprefix("Bearer ")
    with (
        client.websocket_connect(f"/ws/jobs/{job_id}?token={customer_token}") as customer_socket,
        client.websocket_connect(f"/ws/jobs/{job_id}?token={provider_token}") as provider_socket,
    ):
        text_message = client.post(
            f"/jobs/{job_id}/messages",
            json={"body": "I am on my way."},
            headers=provider_headers,
        )
        assert text_message.status_code == 201, text_message.text
        assert customer_socket.receive_json()["message"]["body"] == "I am on my way."
        assert provider_socket.receive_json()["message"]["sender_id"] == provider_user["id"]

        location_message = client.post(
            f"/jobs/{job_id}/messages",
            json={"latitude": 31.52, "longitude": 74.35},
            headers=customer_headers,
        )
        assert location_message.status_code == 201, location_message.text
        assert location_message.json()["sender_id"] == customer_user["id"]
        assert customer_socket.receive_json()["message"]["latitude"] == 31.52
        assert provider_socket.receive_json()["message"]["longitude"] == 74.35

    history = client.get(f"/jobs/{job_id}/messages", headers=customer_headers)
    assert history.status_code == 200
    assert len(history.json()) == 2

    assert client.get(f"/jobs/{job_id}/messages", headers=outsider_headers).status_code == 403
    assert client.post(
        f"/jobs/{job_id}/messages",
        json={"body": "I should not be able to write here"},
        headers=outsider_headers,
    ).status_code == 403


def test_chat_requires_either_text_or_a_complete_location(client, customer, category):
    customer_headers, _ = customer
    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Repair a window", "address": "2 Pine Street"},
        headers=customer_headers,
    ).json()

    assert client.post(f"/jobs/{job['id']}/messages", json={}, headers=customer_headers).status_code == 422
    assert client.post(
        f"/jobs/{job['id']}/messages",
        json={"body": "Here", "latitude": 31.52, "longitude": 74.35},
        headers=customer_headers,
    ).status_code == 422
    assert client.post(
        f"/jobs/{job['id']}/messages",
        json={"latitude": 31.52},
        headers=customer_headers,
    ).status_code == 422
