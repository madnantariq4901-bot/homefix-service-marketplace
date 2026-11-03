from app.core.security import create_access_token, hash_password
from app.database.models.job import Job, JobStatus
from app.database.models.provider import ProviderProfile
from app.database.models.user import User, UserRole


def _admin_headers(db_session):
    admin = User(
        email="job-approach-admin@example.com",
        hashed_password=hash_password("admin-password"),
        full_name="Marketplace Admin",
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    token = create_access_token(admin.id, UserRole.ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


def _make_eligible_provider(client, provider, category, db_session):
    headers, user = provider
    skill = client.post("/providers/me/skills", json={"category_id": category.id}, headers=headers)
    assert skill.status_code == 201, skill.text
    location = client.patch("/providers/me/location", json={"lat": 31.52, "lng": 74.35}, headers=headers)
    assert location.status_code == 200, location.text
    identity = client.post(
        "/providers/me/identity",
        files={
            "id_front": ("front.jpg", b"\xff\xd8\xfffront", "image/jpeg"),
            "id_back": ("back.jpg", b"\xff\xd8\xffback", "image/jpeg"),
            "selfie": ("selfie.jpg", b"\xff\xd8\xffselfie", "image/jpeg"),
        },
        headers=headers,
    )
    assert identity.status_code == 200, identity.text
    profile = db_session.query(ProviderProfile).filter(ProviderProfile.user_id == user["id"]).one()
    profile.is_available = True
    profile.is_verified = True
    db_session.commit()
    return headers, profile


def test_admin_can_invite_eligible_provider_without_assigning_job(
    client, customer, provider, make_user, category, db_session
):
    admin_headers = _admin_headers(db_session)
    customer_headers, _ = customer
    provider_headers, profile = _make_eligible_provider(client, provider, category, db_session)
    job_response = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Repair the front gate", "address": "8 Oak Road"},
        headers=customer_headers,
    )
    assert job_response.status_code == 201, job_response.text
    job_id = job_response.json()["id"]

    denied = client.post(
        f"/jobs/{job_id}/approach",
        json={"provider_id": profile.id},
        headers=customer_headers,
    )
    assert denied.status_code == 403

    invited = client.post(
        f"/jobs/{job_id}/approach",
        json={"provider_id": profile.id},
        headers=admin_headers,
    )
    assert invited.status_code == 201, invited.text
    assert invited.json()["job_id"] == job_id

    provider_notifications = client.get("/notifications/mine", headers=provider_headers)
    assert provider_notifications.status_code == 200
    assert provider_notifications.json()[0]["job_id"] == job_id
    assert "invited you to consider" in provider_notifications.json()[0]["message"]

    job = db_session.query(Job).filter(Job.id == job_id).one()
    assert job.status == JobStatus.REQUESTED
    assert job.provider_id is None

    duplicate = client.post(
        f"/jobs/{job_id}/approach",
        json={"provider_id": profile.id},
        headers=admin_headers,
    )
    assert duplicate.status_code == 409


def test_admin_can_invite_provider_without_job_skill_but_quote_remains_restricted(client, customer, provider, category, db_session):
    admin_headers = _admin_headers(db_session)
    customer_headers, _ = customer
    provider_headers, provider_user = provider
    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Repair a gate", "address": "9 Oak Road"},
        headers=customer_headers,
    ).json()
    profile = db_session.query(ProviderProfile).filter(ProviderProfile.user_id == provider_user["id"]).one()
    profile.is_available = True
    profile.is_verified = True
    db_session.commit()

    directory = client.get("/providers", headers=admin_headers)
    assert directory.status_code == 200
    assert any(item["id"] == profile.id for item in directory.json())

    response = client.post(
        f"/jobs/{job['id']}/approach",
        json={"provider_id": profile.id},
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    viewed = client.get(f"/jobs/{job['id']}", headers=provider_headers)
    assert viewed.status_code == 200
    assert viewed.json()["address"] == "Exact location is shared after a quote is accepted."

    quote = client.post(f"/jobs/{job['id']}/quote", json={"quoted_amount": 50}, headers=provider_headers)
    assert quote.status_code == 403


def test_admin_can_approach_skill_matched_provider_who_is_not_quote_ready(client, customer, provider, category, db_session):
    admin_headers = _admin_headers(db_session)
    customer_headers, _ = customer
    provider_headers, provider_user = provider
    skill = client.post("/providers/me/skills", json={"category_id": category.id}, headers=provider_headers)
    assert skill.status_code == 201, skill.text
    profile = db_session.query(ProviderProfile).filter(ProviderProfile.user_id == provider_user["id"]).one()

    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Install a new tap", "address": "12 Oak Road"},
        headers=customer_headers,
    ).json()
    invited = client.post(
        f"/jobs/{job['id']}/approach",
        json={"provider_id": profile.id},
        headers=admin_headers,
    )

    assert invited.status_code == 201, invited.text
    assert client.get("/notifications/mine", headers=provider_headers).json()[0]["job_id"] == job["id"]


def test_customer_can_target_job_to_one_related_provider(client, customer, provider, make_user, category, db_session):
    customer_headers, _ = customer
    target_headers, target_profile = _make_eligible_provider(client, provider, category, db_session)
    other_headers, _ = make_user(email="other-related-provider@example.com", role="provider")
    other_skill = client.post("/providers/me/skills", json={"category_id": category.id}, headers=other_headers)
    assert other_skill.status_code == 201, other_skill.text

    created = client.post(
        "/jobs",
        json={
            "category_id": category.id,
            "preferred_provider_id": target_profile.id,
            "description": "Repair the kitchen tap",
            "address": "18 Oak Road",
        },
        headers=customer_headers,
    )
    assert created.status_code == 201, created.text
    job_id = created.json()["id"]
    assert created.json()["provider_id"] is None
    assert client.get(f"/jobs/{job_id}", headers=target_headers).status_code == 200
    assert client.get(f"/jobs/{job_id}", headers=other_headers).status_code == 403

    target_feed = client.get("/jobs/available", headers=target_headers)
    other_feed = client.get("/jobs/available", headers=other_headers)
    assert job_id in {job["id"] for job in target_feed.json()}
    assert job_id not in {job["id"] for job in other_feed.json()}
    assert client.get("/notifications/mine", headers=target_headers).json()[0]["job_id"] == job_id
