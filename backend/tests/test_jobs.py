
def _make_provider_ready(client, provider, category, lat=31.52, lng=74.35):
    headers, user = provider
    client.post("/providers/me/skills", json={"category_id": category.id}, headers=headers)
    client.patch("/providers/me/location", json={"lat": lat, "lng": lng}, headers=headers)
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
    return headers, user
 
 
def _verify_provider(db_session, user_id):
    from app.models import ProviderProfile
 
    profile = db_session.query(ProviderProfile).filter(ProviderProfile.user_id == user_id).first()
    profile.is_verified = True
    db_session.commit()
 
 
def _set_provider_available(client, headers):
    response = client.patch("/providers/me/availability", json={"is_available": True}, headers=headers)
    assert response.status_code == 200, response.text


def test_create_job_as_customer(client, customer, category):
    headers, _ = customer
    resp = client.post(
        "/jobs",
        json={
            "category_id": category.id,
            "description": "Leaking kitchen sink",
            "address": "123 Main St",
            "lat": 31.52,
            "lng": 74.35,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "requested"
    assert body["provider_id"] is None  # no verified/available provider yet
 
 
def test_provider_cannot_create_job(client, provider, category):
    headers, _ = provider
    resp = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Fix plumbing", "address": "Test address", "lat": 0, "lng": 0},
        headers=headers,
    )
    assert resp.status_code == 403
 
 
def test_create_job_unknown_category_fails(client, customer):
    headers, _ = customer
    resp = client.post(
        "/jobs",
        json={"category_id": 9999, "description": "Fix plumbing", "address": "Test address", "lat": 0, "lng": 0},
        headers=headers,
    )
    assert resp.status_code == 400
 
 
def test_job_waits_for_customer_to_accept_a_provider_quote(client, customer, provider, category, db_session):
    p_headers, p_user = _make_provider_ready(client, provider, category)
    _verify_provider(db_session, p_user["id"])
    _set_provider_available(client, p_headers)

    c_headers, _ = customer
    resp = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Fix pipe", "address": "addr", "lat": 31.52, "lng": 74.35},
        headers=c_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["provider_id"] is None

    quote = client.post(f"/jobs/{resp.json()['id']}/quote", json={"quoted_amount": 50.0}, headers=p_headers)
    assert quote.status_code == 200
    quotes = client.get(f"/jobs/{resp.json()['id']}/quotes", headers=c_headers)
    assert quotes.status_code == 200
    accepted = client.post(f"/jobs/{resp.json()['id']}/quotes/{quotes.json()[0]['id']}/accept", headers=c_headers)
    assert accepted.status_code == 200
    assert accepted.json()["provider_id"] is not None

 
 
def test_non_participant_cannot_view_job(client, customer, make_user, category):
    c_headers, _ = customer
    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Fix plumbing", "address": "Test address", "lat": 0, "lng": 0},
        headers=c_headers,
    ).json()
 
    outsider_headers, _ = make_user(email="outsider@example.com", role="customer")
    resp = client.get(f"/jobs/{job['id']}", headers=outsider_headers)
    assert resp.status_code == 403


def test_provider_location_is_hidden_until_quote_is_accepted(client, customer, provider, category):
    provider_headers, _ = _make_provider_ready(client, provider, category)
    _set_provider_available(client, provider_headers)
    customer_headers, _ = customer
    job = client.post(
        "/jobs",
        json={
            "category_id": category.id,
            "description": "Repair the kitchen sink",
            "address": "12 Private Street, Lahore",
            "lat": 31.5204,
            "lng": 74.3587,
        },
        headers=customer_headers,
    ).json()

    available = client.get("/jobs/available", headers=provider_headers)
    assert available.status_code == 200
    listed_job = next(item for item in available.json() if item["id"] == job["id"])
    assert listed_job["address"] == "Exact location is shared after a quote is accepted."
    assert listed_job["lat"] is None
    assert listed_job["lng"] is None

    quote = client.post(
        f"/jobs/{job['id']}/quote",
        json={"quoted_amount": 50.0},
        headers=provider_headers,
    )
    assert quote.status_code == 200
    assert quote.json()["address"] == "Exact location is shared after a quote is accepted."
    details = client.get(f"/jobs/{job['id']}", headers=provider_headers)
    assert details.status_code == 200
    assert details.json()["address"] == "Exact location is shared after a quote is accepted."
    assert details.json()["lat"] is None
    assert details.json()["lng"] is None

    customer_details = client.get(f"/jobs/{job['id']}", headers=customer_headers)
    assert customer_details.json()["address"] == "12 Private Street, Lahore"
    assert customer_details.json()["lat"] == 31.5204
    assert customer_details.json()["lng"] == 74.3587

    quotes = client.get(f"/jobs/{job['id']}/quotes", headers=customer_headers)
    accepted = client.post(
        f"/jobs/{job['id']}/quotes/{quotes.json()[0]['id']}/accept",
        headers=customer_headers,
    )
    assert accepted.status_code == 200
    assigned_provider_details = client.get(f"/jobs/{job['id']}", headers=provider_headers)
    assert assigned_provider_details.json()["address"] == "12 Private Street, Lahore"
    assert assigned_provider_details.json()["lat"] == 31.5204
    assert assigned_provider_details.json()["lng"] == 74.3587


def test_quote_and_status_flow_to_completion(client, customer, provider, category, db_session, make_user):
    p_headers, p_user = _make_provider_ready(client, provider, category)
    _verify_provider(db_session, p_user["id"])
    _set_provider_available(client, p_headers)
 
    c_headers, _ = customer
    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Fix pipe", "address": "addr", "lat": 31.52, "lng": 74.35},
        headers=c_headers,
    ).json()
    job_id = job["id"]
    assert job["provider_id"] is None
 
    # provider quotes
    resp = client.post(f"/jobs/{job_id}/quote", json={"quoted_amount": 50.0}, headers=p_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "quoted"
 
    # customer accepts
    resp = client.post(
        f"/jobs/{job_id}/quotes/{client.get(f'/jobs/{job_id}/quotes', headers=c_headers).json()[0]['id']}/accept",
        headers=c_headers,
    )
    assert resp.status_code == 200
 
    # The customer is notified when the provider is on the way.
    resp = client.patch(f"/jobs/{job_id}/status", json={"status": "en_route"}, headers=p_headers)
    assert resp.status_code == 200
    notifications = client.get("/notifications/mine", headers=c_headers)
    assert notifications.status_code == 200
    assert notifications.json()[0]["message"] == f"Your provider is on the way to job #{job_id}."
    customer_notification_id = notifications.json()[0]["id"]
    outsider_headers, _ = make_user(email="outsider@example.com")
    assert client.patch(
        f"/notifications/{customer_notification_id}/read",
        headers=outsider_headers,
    ).status_code == 404
    marked_read = client.patch(
        f"/notifications/{customer_notification_id}/read",
        headers=c_headers,
    )
    assert marked_read.status_code == 200
    assert marked_read.json()["is_read"] is True

    resp = client.patch(f"/jobs/{job_id}/status", json={"status": "in_progress"}, headers=p_headers)
    assert resp.status_code == 200

    # A provider requests completion; the customer must confirm it.
    resp = client.patch(
        f"/jobs/{job_id}/status", json={"status": "completed", "final_amount": 60.0}, headers=p_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    assert resp.json()["completion_requested"] is True
    assert resp.json()["final_amount"] == 60.0
    notifications = client.get("/notifications/mine", headers=c_headers)
    assert any(f"marked job #{job_id} complete" in item["message"] for item in notifications.json())

    confirmed = client.patch(f"/jobs/{job_id}/status", json={"status": "completed"}, headers=c_headers)
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "completed"
    assert confirmed.json()["completion_requested"] is False
    assert client.get("/notifications/mine", headers=p_headers).json()[0]["message"] == (
        f"The customer confirmed completion of job #{job_id}."
    )
 
 
def test_complete_without_final_amount_fails(client, customer, provider, category, db_session):
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
    client.post(
        f"/jobs/{job_id}/quotes/{client.get(f'/jobs/{job_id}/quotes', headers=c_headers).json()[0]['id']}/accept",
        headers=c_headers,
    )
    client.patch(f"/jobs/{job_id}/status", json={"status": "en_route"}, headers=p_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "in_progress"}, headers=p_headers)
 
    resp = client.patch(f"/jobs/{job_id}/status", json={"status": "completed"}, headers=p_headers)
    assert resp.status_code == 400
 
 
def test_invalid_status_transition_rejected(client, customer, category):
    c_headers, _ = customer
    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Fix plumbing", "address": "Test address", "lat": 0, "lng": 0},
        headers=c_headers,
    ).json()
 
    # requested -> accepted is not a valid transition (must go through quoted first)
    resp = client.patch(f"/jobs/{job['id']}/status", json={"status": "accepted"}, headers=c_headers)
    assert resp.status_code == 400
 
 
def test_wrong_role_cannot_set_status(client, customer, provider, category, db_session):
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
 
    # only the customer can accept a quote, not the provider
    resp = client.patch(f"/jobs/{job_id}/status", json={"status": "accepted"}, headers=p_headers)
    assert resp.status_code == 403
 
 
def test_review_flow_updates_provider_rating(client, customer, provider, category, db_session):
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
    client.post(
        f"/jobs/{job_id}/quotes/{client.get(f'/jobs/{job_id}/quotes', headers=c_headers).json()[0]['id']}/accept",
        headers=c_headers,
    )
    client.patch(f"/jobs/{job_id}/status", json={"status": "en_route"}, headers=p_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "in_progress"}, headers=p_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "completed", "final_amount": 60.0}, headers=p_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "completed"}, headers=c_headers)
 
    resp = client.post(f"/jobs/{job_id}/review", json={"rating": 5, "comment": "Great work"}, headers=c_headers)
    assert resp.status_code == 201
 
    profile = client.get("/providers/me", headers=p_headers).json()
    assert profile["rating_avg"] == 5.0
    assert profile["rating_count"] == 1
 
 
def test_review_before_completion_fails(client, customer, category):
    c_headers, _ = customer
    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Fix plumbing", "address": "Test address", "lat": 0, "lng": 0},
        headers=c_headers,
    ).json()
 
    resp = client.post(f"/jobs/{job['id']}/review", json={"rating": 5}, headers=c_headers)
    assert resp.status_code == 400
 
 
def test_review_twice_fails(client, customer, provider, category, db_session):
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
    client.post(
        f"/jobs/{job_id}/quotes/{client.get(f'/jobs/{job_id}/quotes', headers=c_headers).json()[0]['id']}/accept",
        headers=c_headers,
    )
    client.patch(f"/jobs/{job_id}/status", json={"status": "en_route"}, headers=p_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "in_progress"}, headers=p_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "completed", "final_amount": 60.0}, headers=p_headers)
    client.patch(f"/jobs/{job_id}/status", json={"status": "completed"}, headers=c_headers)
 
    client.post(f"/jobs/{job_id}/review", json={"rating": 5}, headers=c_headers)
    resp = client.post(f"/jobs/{job_id}/review", json={"rating": 3}, headers=c_headers)
    assert resp.status_code == 400
 


def test_unassigned_job_can_receive_and_accept_a_quote(client, customer, provider, category, db_session):
    c_headers, _ = customer
    p_headers, p_user = provider

    job_response = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Repair a tap", "address": "45 Main Road"},
        headers=c_headers,
    )
    assert job_response.status_code == 201, job_response.text
    job = job_response.json()
    assert job["provider_id"] is None

    _make_provider_ready(client, provider, category)
    _verify_provider(db_session, p_user["id"])
    _set_provider_available(client, p_headers)

    available = client.get("/jobs/available", headers=p_headers)
    assert available.status_code == 200, available.text
    assert any(item["id"] == job["id"] for item in available.json())

    quote_response = client.post(
        f"/jobs/{job['id']}/quote",
        json={"quoted_amount": 75},
        headers=p_headers,
    )
    assert quote_response.status_code == 200, quote_response.text
    assert quote_response.json()["status"] == "quoted"

    quotes_response = client.get(f"/jobs/{job['id']}/quotes", headers=c_headers)
    assert quotes_response.status_code == 200, quotes_response.text
    assert len(quotes_response.json()) == 1

    quote_id = quotes_response.json()[0]["id"]
    accepted = client.post(f"/jobs/{job['id']}/quotes/{quote_id}/accept", headers=c_headers)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "accepted"
    assert accepted.json()["quoted_amount"] == 75


def test_admin_can_delete_cancelled_and_accepted_jobs(client, customer, provider, category, db_session):
    from app.core.security import create_access_token, hash_password
    from app.database.models.quote import Quote
    from app.database.models.user import User, UserRole

    customer_headers, _ = customer
    provider_headers, provider_user = _make_provider_ready(client, provider, category)
    _verify_provider(db_session, provider_user["id"])
    _set_provider_available(client, provider_headers)

    job_ids = []
    for description in ("Cancelled request", "Confirmed request"):
        response = client.post(
            "/jobs",
            json={"category_id": category.id, "description": description, "address": "Test address"},
            headers=customer_headers,
        )
        assert response.status_code == 201, response.text
        job_ids.append(response.json()["id"])

    cancelled = client.patch(
        f"/jobs/{job_ids[0]}/status",
        json={"status": "cancelled"},
        headers=customer_headers,
    )
    assert cancelled.status_code == 200, cancelled.text

    quote_response = client.post(
        f"/jobs/{job_ids[1]}/quote",
        json={"quoted_amount": 75},
        headers=provider_headers,
    )
    assert quote_response.status_code == 200, quote_response.text
    quotes = client.get(f"/jobs/{job_ids[1]}/quotes", headers=customer_headers)
    accepted = client.post(
        f"/jobs/{job_ids[1]}/quotes/{quotes.json()[0]['id']}/accept",
        headers=customer_headers,
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "accepted"

    admin = User(
        email="job-admin@example.com",
        hashed_password=hash_password("admin-password"),
        full_name="Job Admin",
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    admin_headers = {"Authorization": f"Bearer {create_access_token(admin.id, UserRole.ADMIN.value)}"}

    denied = client.delete(f"/jobs/{job_ids[0]}", headers=customer_headers)
    assert denied.status_code == 403

    for job_id in job_ids:
        response = client.delete(f"/jobs/{job_id}", headers=admin_headers)
        assert response.status_code == 204
        assert client.get(f"/jobs/{job_id}", headers=admin_headers).status_code == 404
    assert db_session.query(Quote).filter(Quote.job_id == job_ids[1]).count() == 0


def test_provider_without_matching_skill_cannot_quote(client, customer, provider, category):
    c_headers, _ = customer
    p_headers, _ = provider
    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Repair a tap", "address": "45 Main Road"},
        headers=c_headers,
    ).json()

    resp = client.post(f"/jobs/{job['id']}/quote", json={"quoted_amount": 75}, headers=p_headers)
    assert resp.status_code == 403


def test_provider_can_browse_but_must_submit_identity_before_quoting(client, customer, provider, category):
    c_headers, _ = customer
    p_headers, _ = provider
    client.post("/providers/me/skills", json={"category_id": category.id}, headers=p_headers)
    available = client.patch("/providers/me/availability", json={"is_available": True}, headers=p_headers)
    assert available.status_code == 200

    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Repair a tap", "address": "45 Main Road"},
        headers=c_headers,
    ).json()

    available_jobs = client.get("/jobs/available", headers=p_headers)
    assert any(item["id"] == job["id"] for item in available_jobs.json())
    assert client.get(f"/jobs/{job['id']}", headers=p_headers).status_code == 200

    quote = client.post(f"/jobs/{job['id']}/quote", json={"quoted_amount": 75}, headers=p_headers)
    assert quote.status_code == 403
    assert "identity documents" in quote.json()["detail"]


def test_provider_can_browse_matching_jobs_while_unavailable(client, customer, provider, category):
    c_headers, _ = customer
    p_headers, _ = provider
    client.post("/providers/me/skills", json={"category_id": category.id}, headers=p_headers)

    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Repair a tap", "address": "45 Main Road"},
        headers=c_headers,
    ).json()

    available_jobs = client.get("/jobs/available", headers=p_headers)
    assert available_jobs.status_code == 200, available_jobs.text
    assert any(item["id"] == job["id"] for item in available_jobs.json())
    assert client.get(f"/jobs/{job['id']}", headers=p_headers).status_code == 200

    quote = client.post(f"/jobs/{job['id']}/quote", json={"quoted_amount": 75}, headers=p_headers)
    assert quote.status_code == 403


def test_provider_job_feeds_only_include_their_skill_categories(client, customer, provider, category, db_session):
    from app.database.models.category import ServiceCategory
    from app.database.models.job import Job, JobStatus
    from app.database.models.provider import ProviderProfile

    customer_headers, customer_user = customer
    provider_headers, provider_user = provider
    client.post("/providers/me/skills", json={"category_id": category.id}, headers=provider_headers)
    profile = db_session.query(ProviderProfile).filter(ProviderProfile.user_id == provider_user["id"]).one()
    other_category = ServiceCategory(name="electrician", base_hourly_rate=30.0, description="Electrical work")
    db_session.add(other_category)
    db_session.commit()
    db_session.refresh(other_category)

    matching_open = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Fix a leaking tap", "address": "1 Oak Road"},
        headers=customer_headers,
    ).json()
    unrelated_open = client.post(
        "/jobs",
        json={"category_id": other_category.id, "description": "Replace a socket", "address": "2 Oak Road"},
        headers=customer_headers,
    ).json()

    available = client.get("/jobs/available", headers=provider_headers)
    available_ids = {job["id"] for job in available.json()}
    assert matching_open["id"] in available_ids
    assert unrelated_open["id"] not in available_ids

    matching_assigned = Job(
        customer_id=customer_user["id"],
        provider_id=profile.id,
        category_id=category.id,
        description="Completed plumbing repair",
        address="3 Oak Road",
        status=JobStatus.ACCEPTED,
    )
    unrelated_assigned = Job(
        customer_id=customer_user["id"],
        provider_id=profile.id,
        category_id=other_category.id,
        description="Assigned electrical work",
        address="4 Oak Road",
        status=JobStatus.ACCEPTED,
    )
    db_session.add_all([matching_assigned, unrelated_assigned])
    db_session.commit()
    db_session.refresh(matching_assigned)
    db_session.refresh(unrelated_assigned)

    mine = client.get("/jobs/mine", headers=provider_headers)
    mine_ids = {job["id"] for job in mine.json()}
    assert matching_assigned.id in mine_ids
    assert unrelated_assigned.id not in mine_ids


def test_fifth_completed_job_automatically_verifies_provider(client, customer, provider, category, db_session):
    from app.database.models.job import Job, JobStatus
    from app.database.models.provider import ProviderProfile

    p_headers, p_user = provider
    c_headers, c_user = customer
    client.post("/providers/me/skills", json={"category_id": category.id}, headers=p_headers)
    profile = client.get("/providers/me", headers=p_headers).json()

    for index in range(4):
        db_session.add(
            Job(
                customer_id=c_user["id"],
                provider_id=profile["id"],
                category_id=category.id,
                description=f"Previous completed job {index}",
                address="Test address",
                status=JobStatus.COMPLETED,
            )
        )
    current_job = Job(
        customer_id=c_user["id"],
        provider_id=profile["id"],
        category_id=category.id,
        description="Fifth completed job",
        address="Test address",
        status=JobStatus.IN_PROGRESS,
    )
    db_session.add(current_job)
    db_session.commit()

    response = client.patch(
        f"/jobs/{current_job.id}/status",
        json={"status": "completed", "final_amount": 75},
        headers=p_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "in_progress"
    assert response.json()["completion_requested"] is True

    refreshed = client.get("/providers/me", headers=p_headers).json()
    assert refreshed["completed_job_count"] == 4
    assert refreshed["is_verified"] is False

    response = client.patch(
        f"/jobs/{current_job.id}/status",
        json={"status": "completed"},
        headers=c_headers,
    )
    assert response.status_code == 200, response.text
    refreshed = client.get("/providers/me", headers=p_headers).json()
    assert refreshed["completed_job_count"] == 5
    assert refreshed["is_verified"] is True

    db_profile = db_session.query(ProviderProfile).filter(ProviderProfile.id == profile["id"]).one()
    assert db_profile.is_verified is True
    recommended = client.get("/providers/public").json()
    assert any(item["id"] == profile["id"] for item in recommended)
