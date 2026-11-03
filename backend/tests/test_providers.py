
def test_get_own_profile_as_provider(client, provider):
    headers, _ = provider
    resp = client.get("/providers/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["skills"] == []
 
 
def test_customer_cannot_access_provider_me(client, customer):
    headers, _ = customer
    resp = client.get("/providers/me", headers=headers)
    assert resp.status_code == 403
 
 
def test_add_skill_success(client, provider, category):
    headers, _ = provider
    resp = client.post(
        "/providers/me/skills",
        json={"category_id": category.id, "years_experience": 5},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["category_id"] == category.id
    assert resp.json()["years_experience"] == 5
 
 

def test_unverified_provider_can_mark_available_before_identity_submission(client, provider):
    headers, _ = provider
    response = client.patch("/providers/me/availability", json={"is_available": True}, headers=headers)
    assert response.status_code == 200
    assert response.json()["is_available"] is True


def test_identity_submission_stores_private_files_and_exposes_only_submission_status(
    client, provider, monkeypatch, tmp_path
):
    from app.config import settings

    monkeypatch.setattr(settings, "IDENTITY_UPLOAD_DIR", tmp_path)
    headers, _ = provider
    response = client.post(
        "/providers/me/identity",
        files={
            "id_front": ("front.jpg", b"\xff\xd8\xfffront", "image/jpeg"),
            "id_back": ("back.jpg", b"\xff\xd8\xffback", "image/jpeg"),
            "selfie": ("selfie.jpg", b"\xff\xd8\xffselfie", "image/jpeg"),
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json()["identity_documents_submitted"] is True
    assert len(list(tmp_path.iterdir())) == 3
    assert all(path.stat().st_mode & 0o777 == 0o600 for path in tmp_path.iterdir())
    assert not any("path" in key for key in response.json())

    duplicate = client.post(
        "/providers/me/identity",
        files={
            "id_front": ("front.jpg", b"\xff\xd8\xfffront", "image/jpeg"),
            "id_back": ("back.jpg", b"\xff\xd8\xffback", "image/jpeg"),
            "selfie": ("selfie.jpg", b"\xff\xd8\xffselfie", "image/jpeg"),
        },
        headers=headers,
    )
    assert duplicate.status_code == 409


def test_admin_directory_shows_document_submission_without_public_exposure(client, provider, db_session):
    from app.core.security import create_access_token
    from app.core.security import hash_password
    from app.database.models.provider import ProviderProfile
    from app.database.models.user import User, UserRole

    provider_headers, provider_user = provider
    uploaded = client.post(
        "/providers/me/identity",
        files={
            "id_front": ("front.jpg", b"\xff\xd8\xfffront", "image/jpeg"),
            "id_back": ("back.jpg", b"\xff\xd8\xffback", "image/jpeg"),
            "selfie": ("selfie.jpg", b"\xff\xd8\xffselfie", "image/jpeg"),
        },
        headers=provider_headers,
    )
    assert uploaded.status_code == 200
    profile_id = uploaded.json()["id"]
    profile = db_session.query(ProviderProfile).filter(ProviderProfile.id == profile_id).one()
    profile.is_verified = True

    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("admin-password"),
        full_name="Admin",
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    admin_headers = {"Authorization": f"Bearer {create_access_token(admin.id, UserRole.ADMIN.value)}"}

    admin_list = client.get("/providers", headers=admin_headers)
    assert admin_list.status_code == 200
    provider_item = next(item for item in admin_list.json() if item["id"] == profile_id)
    assert provider_item["identity_documents_submitted"] is True

    public_detail = client.get(f"/providers/{profile_id}")
    assert public_detail.status_code == 200
    assert "identity_documents_submitted" not in public_detail.json()


# ---- public directory (verified providers only) ----

def _verify_provider(db_session, user_id):
    from app.database.models.provider import ProviderProfile

    profile = db_session.query(ProviderProfile).filter(ProviderProfile.user_id == user_id).one()
    profile.is_verified = True
    db_session.commit()
    return profile


def test_public_directory_hides_unverified_providers(client, provider, category):
    headers, _ = provider
    client.post("/providers/me/skills", json={"category_id": category.id, "years_experience": 3}, headers=headers)
    resp = client.get("/providers/public")
    assert resp.status_code == 200
    assert resp.json() == []


def test_public_directory_lists_verified_provider_without_private_fields(client, provider, category, db_session):
    headers, user = provider
    client.post("/providers/me/skills", json={"category_id": category.id, "years_experience": 3}, headers=headers)
    profile = _verify_provider(db_session, user["id"])

    resp = client.get("/providers/public")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["skills"][0]["category"] == "plumber"
    assert data[0]["skills"][0]["years_experience"] == 3
    for private_field in (
        "user_id",
        "current_lat",
        "current_lng",
        "email",
        "phone",
        "identity_front_path",
        "identity_back_path",
        "identity_selfie_path",
        "identity_documents_submitted",
    ):
        assert private_field not in data[0]

    detail = client.get(f"/providers/public/{profile.id}")
    assert detail.status_code == 200
    assert detail.json()["full_name"] == "Test User"


def test_public_directory_filters_by_category(client, provider, category, db_session):
    headers, user = provider
    client.post("/providers/me/skills", json={"category_id": category.id, "years_experience": 1}, headers=headers)
    _verify_provider(db_session, user["id"])

    assert len(client.get("/providers/public", params={"category": "plumber"}).json()) == 1
    assert client.get("/providers/public", params={"category": "electrician"}).json() == []


def test_public_directory_supports_search_and_server_pagination(client, provider, category, db_session, make_user):
    headers, user = provider
    client.post("/providers/me/skills", json={"category_id": category.id, "years_experience": 3}, headers=headers)
    first_profile = _verify_provider(db_session, user["id"])

    second_headers, second_user = make_user(
        email="another-provider@example.com",
        full_name="Avery Provider",
        role="provider",
    )
    client.post(
        "/providers/me/skills",
        json={"category_id": category.id, "years_experience": 8},
        headers=second_headers,
    )
    _verify_provider(db_session, second_user["id"])

    filtered = client.get("/providers/public", params={"search": "Avery"})
    assert filtered.status_code == 200
    assert [item["full_name"] for item in filtered.json()] == ["Avery Provider"]
    assert len(client.get("/providers/public", params={"search": "plumber"}).json()) == 2

    page = client.get("/providers/public", params={"limit": 1, "offset": 1, "sort_by": "name"})
    assert page.status_code == 200
    assert len(page.json()) == 1
    assert page.json()[0]["id"] == first_profile.id
    most_experienced = client.get("/providers/public", params={"limit": 1, "sort_by": "experience"})
    assert most_experienced.json()[0]["full_name"] == "Avery Provider"


def test_public_provider_detail_404_when_unverified(client, provider):
    headers, _ = provider
    client.get("/providers/me", headers=headers)  # creates the (unverified) profile
    assert client.get("/providers/public/1").status_code == 404


def test_recommended_directory_prioritizes_completed_jobs(client, provider, category, customer, db_session, make_user):
    from app.database.models.job import Job, JobStatus
    from app.database.models.provider import ProviderProfile

    first_headers, first_user = provider
    client.post("/providers/me/skills", json={"category_id": category.id}, headers=first_headers)
    first_profile = _verify_provider(db_session, first_user["id"])
    first_profile.rating_avg = 5.0
    db_session.commit()

    second_headers, second_user = make_user(
        email="experienced-provider@example.com",
        full_name="Experienced Provider",
        role="provider",
    )
    client.post("/providers/me/skills", json={"category_id": category.id}, headers=second_headers)
    second_profile = db_session.query(ProviderProfile).filter(
        ProviderProfile.user_id == second_user["id"]
    ).one()
    second_profile.is_verified = True
    db_session.commit()

    _, customer_user = customer
    for index in range(2):
        db_session.add(
            Job(
                customer_id=customer_user["id"],
                provider_id=second_profile.id,
                category_id=category.id,
                description=f"Completed work {index}",
                address="Test address",
                status=JobStatus.COMPLETED,
            )
        )
    db_session.commit()

    response = client.get("/providers/public")
    assert response.status_code == 200, response.text
    assert response.json()[0]["id"] == second_profile.id
    assert response.json()[0]["completed_job_count"] == 2
