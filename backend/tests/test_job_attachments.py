def _create_job(client, customer, category):
    headers, _ = customer
    response = client.post(
        "/jobs",
        json={"category_id": category.id, "description": "Repair a broken cabinet", "address": "12 Oak Road"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return headers, response.json()["id"]


def test_customer_can_upload_and_job_participants_can_view_attachments(client, customer, provider, make_user, category):
    customer_headers, job_id = _create_job(client, customer, category)
    provider_headers, _ = provider
    skill = client.post("/providers/me/skills", json={"category_id": category.id}, headers=provider_headers)
    assert skill.status_code == 201, skill.text
    uploaded = client.post(
        f"/jobs/{job_id}/attachments",
        files=[
            ("files", ("cabinet.jpg", b"\xff\xd8\xffimage-data", "image/jpeg")),
            ("files", ("detail.png", b"\x89PNG\r\n\x1a\nimage-data", "image/png")),
            ("files", ("repair.webm", b"\x1a\x45\xdf\xa3video-data", "video/webm")),
        ],
        headers=customer_headers,
    )
    assert uploaded.status_code == 201, uploaded.text
    assert [item["original_name"] for item in uploaded.json()] == ["cabinet.jpg", "detail.png", "repair.webm"]
    assert all("stored_path" not in item for item in uploaded.json())

    job = client.get(f"/jobs/{job_id}", headers=customer_headers)
    assert job.status_code == 200
    assert len(job.json()["attachments"]) == 3

    image = client.get(
        f"/jobs/{job_id}/attachments/{uploaded.json()[0]['id']}/file",
        headers=customer_headers,
    )
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"
    assert image.content == b"\xff\xd8\xffimage-data"

    provider_job = client.get(f"/jobs/{job_id}", headers=provider_headers)
    assert provider_job.status_code == 200
    video_attachment = next(item for item in provider_job.json()["attachments"] if item["media_type"] == "video/webm")
    video = client.get(
        f"/jobs/{job_id}/attachments/{video_attachment['id']}/file",
        headers=provider_headers,
    )
    assert video.status_code == 200
    assert video.headers["content-type"] == "video/webm"
    assert video.content == b"\x1a\x45\xdf\xa3video-data"

    outsider_headers, _ = make_user(email="attachment-outsider@example.com", role="customer")
    denied = client.get(
        f"/jobs/{job_id}/attachments/{uploaded.json()[0]['id']}/file",
        headers=outsider_headers,
    )
    assert denied.status_code == 403


def test_only_job_owner_can_upload_valid_image_or_video_files(client, customer, provider, category):
    customer_headers, job_id = _create_job(client, customer, category)
    provider_headers, _ = provider
    denied = client.post(
        f"/jobs/{job_id}/attachments",
        files=[("files", ("provider.jpg", b"\xff\xd8\xffimage-data", "image/jpeg"))],
        headers=provider_headers,
    )
    assert denied.status_code == 403

    invalid = client.post(
        f"/jobs/{job_id}/attachments",
        files=[("files", ("payload.txt", b"not an image", "text/plain"))],
        headers=customer_headers,
    )
    assert invalid.status_code == 400


def test_job_attachment_upload_enforces_file_count(client, customer, category):
    customer_headers, job_id = _create_job(client, customer, category)
    files = [
        ("files", (f"photo-{index}.jpg", b"\xff\xd8\xffdata", "image/jpeg"))
        for index in range(6)
    ]
    response = client.post(f"/jobs/{job_id}/attachments", files=files, headers=customer_headers)
    assert response.status_code == 413
