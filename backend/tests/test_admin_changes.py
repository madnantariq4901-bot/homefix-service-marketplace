from app.core.security import create_access_token, hash_password
from app.database.models.user import User, UserRole


def _admin_headers(db_session):
    admin = User(
        email="admin-changes@example.com",
        hashed_password=hash_password("admin-password"),
        full_name="Marketplace Admin",
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.commit()
    token = create_access_token(admin.id, UserRole.ADMIN.value)
    return {"Authorization": f"Bearer {token}"}


def test_customer_and_admin_can_edit_owned_job_but_outsider_cannot(client, customer, make_user, category, db_session):
    admin_headers = _admin_headers(db_session)
    customer_headers, _ = customer
    created = client.post(
        "/jobs",
        json={
            "category_id": category.id,
            "description": "Repair a leaking tap",
            "address": "12 Market Street",
            "lat": 31.52,
            "lng": 74.35,
        },
        headers=customer_headers,
    )
    job_id = created.json()["id"]
    changes = {
        "description": "Replace the kitchen faucet",
        "address": "18 Market Street",
        "lat": 31.53,
        "lng": 74.36,
    }

    customer_update = client.patch(f"/jobs/{job_id}", json=changes, headers=customer_headers)
    assert customer_update.status_code == 200, customer_update.text

    outsider_headers, _ = make_user(email="job-outsider@example.com", role="customer")
    denied = client.patch(f"/jobs/{job_id}", json=changes, headers=outsider_headers)
    assert denied.status_code == 403

    updated = client.patch(f"/jobs/{job_id}", json=changes, headers=admin_headers)
    assert updated.status_code == 200, updated.text
    assert updated.json()["description"] == changes["description"]
    assert updated.json()["address"] == changes["address"]
    assert updated.json()["lat"] == changes["lat"]
    assert updated.json()["lng"] == changes["lng"]

    unknown_category = client.patch(
        f"/jobs/{job_id}",
        json={"category_id": 9999},
        headers=admin_headers,
    )
    assert unknown_category.status_code == 400


def test_assigned_provider_can_edit_job_but_unassigned_provider_cannot(
    client, customer, provider, make_user, category, db_session
):
    from app.database.models.job import Job

    customer_headers, _ = customer
    provider_headers, _ = provider
    profile = client.patch(
        "/providers/me/location",
        json={"lat": 31.52, "lng": 74.35},
        headers=provider_headers,
    )
    assert profile.status_code == 200, profile.text

    created = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Repair a door", "address": "8 Oak Road"},
        headers=customer_headers,
    )
    job_id = created.json()["id"]
    job = db_session.query(Job).filter(Job.id == job_id).one()
    job.provider_id = profile.json()["id"]
    db_session.commit()

    changes = {"description": "Repair the front door"}
    updated = client.patch(f"/jobs/{job_id}", json=changes, headers=provider_headers)
    assert updated.status_code == 200, updated.text
    assert updated.json()["description"] == changes["description"]

    outsider_headers, _ = make_user(email="other-provider@example.com", role="provider")
    denied = client.patch(f"/jobs/{job_id}", json=changes, headers=outsider_headers)
    assert denied.status_code == 403


def test_admin_can_manage_services_without_orphaning_jobs(client, customer, category, db_session):
    admin_headers = _admin_headers(db_session)
    customer_headers, _ = customer
    job = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Repair a sink", "address": "12 Market Street"},
        headers=customer_headers,
    ).json()

    changes = {"base_hourly_rate": 42.5, "description": "Updated plumbing service details"}
    denied = client.patch(f"/categories/{category.id}", json=changes, headers=customer_headers)
    assert denied.status_code == 403

    updated = client.patch(f"/categories/{category.id}", json=changes, headers=admin_headers)
    assert updated.status_code == 200, updated.text
    assert updated.json()["base_hourly_rate"] == changes["base_hourly_rate"]
    assert updated.json()["description"] == changes["description"]

    in_use = client.delete(f"/categories/{category.id}", headers=admin_headers)
    assert in_use.status_code == 409
    assert client.get(f"/jobs/{job['id']}", headers=admin_headers).status_code == 200

    created = client.post(
        "/categories",
        json={"name": "Window Cleaning", "base_hourly_rate": 50, "description": "Exterior and interior glass"},
        headers=admin_headers,
    )
    assert created.status_code == 201, created.text
    assert created.json()["name"] == "Window Cleaning"
    removed = client.delete(f"/categories/{created.json()['id']}", headers=admin_headers)
    assert removed.status_code == 204
