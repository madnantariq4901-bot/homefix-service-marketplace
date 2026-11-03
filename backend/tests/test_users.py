# tests/test_users.py
def test_read_my_user(client, customer):
    headers, user = customer
    resp = client.get("/users/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == user["email"]


def test_read_my_user_without_token_fails(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_update_my_profile(client, customer):
    headers, _ = customer
    resp = client.patch(
        "/users/me",
        headers=headers,
        json={"full_name": "  Updated Customer  ", "phone": " 123-456 "},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Customer"
    assert resp.json()["phone"] == "123-456"


def test_update_my_profile_can_clear_phone(client, customer):
    headers, _ = customer
    resp = client.patch("/users/me", headers=headers, json={"phone": " "})
    assert resp.status_code == 200
    assert resp.json()["phone"] is None


def test_update_my_profile_rejects_invalid_or_empty_update(client, customer):
    headers, _ = customer
    assert client.patch("/users/me", headers=headers, json={}).status_code == 422
    assert client.patch("/users/me", headers=headers, json={"full_name": " "}).status_code == 422


def test_update_my_profile_does_not_allow_role_or_email_changes(client, customer):
    headers, user = customer
    resp = client.patch(
        "/users/me",
        headers=headers,
        json={"role": "admin", "email": "attacker@example.com"},
    )
    assert resp.status_code == 422
    assert client.get("/users/me", headers=headers).json()["role"] == user["role"]


def test_update_my_profile_requires_authentication(client):
    resp = client.patch("/users/me", json={"full_name": "Updated User"})
    assert resp.status_code == 401