from app.database.models.job import Job
from app.database.models.user import User, UserRole
from app.schemas.job import JobOut


def job_response_for_user(job: Job, current_user: User) -> JobOut:
    """Return permitted job data. Names are visible to authorized viewers; emails only to participants/admin."""
    is_customer = job.customer_id == current_user.id
    is_assigned_provider = bool(
        job.provider is not None and job.provider.user_id == current_user.id
    )
    is_admin = current_user.role == UserRole.ADMIN
    can_view_contact_details = is_customer or is_assigned_provider or is_admin

    customer = job.customer
    provider_user = job.provider.user if job.provider is not None else None
    updates = {
        # Providers considering an open job can see the poster's name, but not email/phone.
        "customer_name": customer.full_name if customer is not None else None,
        "customer_email": customer.email if can_view_contact_details and customer is not None else None,
        # Provider identity/contact information is shared only after assignment, or with admin.
        "provider_name": provider_user.full_name if can_view_contact_details and provider_user is not None else None,
        "provider_email": provider_user.email if can_view_contact_details and provider_user is not None else None,
        # Whether a review has already been submitted for this job (server-authoritative).
        "has_review": job.review is not None,
    }
    if current_user.role == UserRole.PROVIDER and not is_assigned_provider:
        updates.update({
            "address": "Exact location is shared after a quote is accepted.",
            "lat": None,
            "lng": None,
        })
    return JobOut.model_validate(job).model_copy(update=updates)
