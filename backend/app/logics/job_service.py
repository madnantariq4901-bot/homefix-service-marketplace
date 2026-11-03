import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status # pyright: ignore[reportMissingImports]
from sqlalchemy import or_ # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.models.category import ServiceCategory
from app.database.models.job import Job, JobStatus
from app.database.models.job_attachment import JobAttachment
from app.database.models.job_invitation import JobInvitation
from app.database.models.notification import Notification
from app.database.models.provider import ProviderProfile, ProviderSkill
from app.database.models.quote import Quote
from app.database.models.review import Review
from app.database.models.user import User, UserRole
from app.config import settings
from app.logics.job_state import InvalidTransitionError, validate_transition
from app.schemas.job import JobAdminUpdate, JobCreate, JobStatusUpdate
from app.schemas.quote import QuoteCreate

MAX_JOB_ATTACHMENT_BYTES = 20 * 1024 * 1024
MAX_JOB_ATTACHMENTS = 5
MAX_JOB_ATTACHMENT_TOTAL_BYTES = 50 * 1024 * 1024

ATTACHMENT_FORMATS = {
    "image/jpeg": (".jpg", lambda data: data.startswith(b"\xff\xd8\xff")),
    "image/png": (".png", lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
    "image/webp": (".webp", lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"),
    "video/mp4": (".mp4", lambda data: len(data) >= 12 and data[4:8] == b"ftyp"),
    "video/quicktime": (".mov", lambda data: len(data) >= 12 and data[4:8] == b"ftyp"),
    "video/webm": (".webm", lambda data: data.startswith(b"\x1a\x45\xdf\xa3")),
}


def _provider_profile_for(db: Session, user: User):
    return db.query(ProviderProfile).filter(ProviderProfile.user_id == user.id).first()


def create_job(db: Session, customer: User, payload: JobCreate) -> Job:
    category = db.query(ServiceCategory).filter(ServiceCategory.id == payload.category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category")

    preferred_provider = None
    if payload.preferred_provider_id is not None:
        preferred_provider = db.query(ProviderProfile).filter(
            ProviderProfile.id == payload.preferred_provider_id,
        ).first()
        if preferred_provider is None or not preferred_provider.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a listed provider")
        provider_has_skill = db.query(ProviderSkill.id).filter(
            ProviderSkill.provider_id == preferred_provider.id,
            ProviderSkill.category_id == category.id,
        ).first()
        if provider_has_skill is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This provider does not offer the selected service")

    job = Job(
        customer_id=customer.id,
        target_provider_id=preferred_provider.id if preferred_provider else None,
        category_id=payload.category_id,
        description=payload.description.strip(),
        address=payload.address.strip(),
        lat=payload.lat,
        lng=payload.lng,
        status=JobStatus.REQUESTED,
    )
    db.add(job)
    db.flush()
    if preferred_provider is not None:
        message = f"You were selected as the preferred provider for job #{job.id}. Review the details and submit a quote if interested."
        db.add(JobInvitation(job_id=job.id, provider_id=preferred_provider.id, invited_by_user_id=customer.id))
        db.add(Notification(user_id=preferred_provider.user_id, job_id=job.id, message=message))
    db.commit()
    db.refresh(job)
    return job


def add_job_attachments(
    db: Session,
    job_id: int,
    actor: User,
    uploads: list[tuple[str, str, bytes]],
) -> list[JobAttachment]:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if actor.role != UserRole.ADMIN and job.customer_id != actor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the job owner can add attachments")
    if not uploads:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose at least one file")
    existing_count = db.query(JobAttachment.id).filter(JobAttachment.job_id == job_id).count()
    if existing_count + len(uploads) > MAX_JOB_ATTACHMENTS:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="A job can have at most 5 attachments")
    if sum(len(data) for _, _, data in uploads) > MAX_JOB_ATTACHMENT_TOTAL_BYTES:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Attachments must total 50 MB or less")

    directory = settings.IDENTITY_UPLOAD_DIR / "job_media" / str(job_id)
    stored_paths: list[Path] = []
    attachments: list[JobAttachment] = []
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
        for original_name, content_type, contents in uploads:
            if not contents:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attachments cannot be empty")
            if len(contents) > MAX_JOB_ATTACHMENT_BYTES:
                raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="Each attachment must be 20 MB or smaller")

            media_type = content_type.split(";", 1)[0].strip().lower()
            file_format = ATTACHMENT_FORMATS.get(media_type)
            if file_format is None or not file_format[1](contents):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Use JPEG, PNG, or WebP images, or MP4, MOV, or WebM videos",
                )

            safe_name = Path(original_name or "attachment").name.replace("\x00", "")[:255] or "attachment"
            extension = file_format[0]
            path = directory / f"{uuid4().hex}{extension}"
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stored_file:
                stored_file.write(contents)
            stored_paths.append(path)
            attachments.append(
                JobAttachment(
                    job_id=job_id,
                    original_name=safe_name,
                    stored_path=str(path),
                    media_type=media_type,
                    size_bytes=len(contents),
                )
            )

        db.add_all(attachments)
        db.commit()
        for attachment in attachments:
            db.refresh(attachment)
        return attachments
    except Exception:
        db.rollback()
        for path in stored_paths:
            path.unlink(missing_ok=True)
        raise


def get_job_attachment(db: Session, job_id: int, attachment_id: int) -> JobAttachment:
    attachment = db.query(JobAttachment).filter(
        JobAttachment.id == attachment_id,
        JobAttachment.job_id == job_id,
    ).first()
    if attachment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    if not Path(attachment.stored_path).is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file not found")
    return attachment


def delete_job(db: Session, job_id: int) -> None:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    attachments = db.query(JobAttachment).filter(JobAttachment.job_id == job_id).all()
    db.query(JobAttachment).filter(JobAttachment.job_id == job_id).delete(synchronize_session=False)
    db.query(Quote).filter(Quote.job_id == job_id).delete(synchronize_session=False)
    db.query(Review).filter(Review.job_id == job_id).delete(synchronize_session=False)
    db.query(JobInvitation).filter(JobInvitation.job_id == job_id).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.job_id == job_id).delete(synchronize_session=False)
    db.delete(job)
    db.commit()
    for attachment in attachments:
        Path(attachment.stored_path).unlink(missing_ok=True)


def update_job_details(db: Session, job_id: int, actor: User, payload: JobAdminUpdate) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    profile = _provider_profile_for(db, actor)
    is_owner = job.customer_id == actor.id
    is_assigned_provider = bool(profile and job.provider_id == profile.id)
    if not (actor.role == UserRole.ADMIN or is_owner or is_assigned_provider):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to edit this job")

    changes = payload.model_dump(exclude_unset=True)
    if "category_id" in changes:
        category = db.query(ServiceCategory).filter(ServiceCategory.id == changes["category_id"]).first()
        if category is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category")
    for field, value in changes.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


def _provider_can_quote(db: Session, profile: ProviderProfile, job: Job) -> bool:
    skill = (
        db.query(ProviderSkill)
        .filter(ProviderSkill.provider_id == profile.id, ProviderSkill.category_id == job.category_id)
        .first()
    )
    return bool(profile.is_available and profile.identity_documents_submitted and skill is not None)


def approach_provider(db: Session, job_id: int, provider_id: int, invited_by: User) -> dict:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status not in (JobStatus.REQUESTED, JobStatus.QUOTED) or job.provider_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This job is no longer accepting provider invitations")
    if job.target_provider_id is not None and job.target_provider_id != provider_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This job was requested from another provider")

    profile = db.query(ProviderProfile).filter(ProviderProfile.id == provider_id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    existing = db.query(JobInvitation).filter(
        JobInvitation.job_id == job.id,
        JobInvitation.provider_id == profile.id,
    ).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This provider has already been invited")

    message = f"An administrator invited you to consider job #{job.id}. Review the details and submit a quote if interested."
    invitation = JobInvitation(job_id=job.id, provider_id=profile.id, invited_by_user_id=invited_by.id)
    notification = Notification(user_id=profile.user_id, job_id=job.id, message=message)
    db.add(invitation)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return {
        "job_id": job.id,
        "provider_id": profile.id,
        "notification_id": notification.id,
        "message": message,
    }


def _provider_can_browse_job(db: Session, profile: ProviderProfile, job: Job) -> bool:
    skill = (
        db.query(ProviderSkill)
        .filter(ProviderSkill.provider_id == profile.id, ProviderSkill.category_id == job.category_id)
        .first()
    )
    return skill is not None


def get_job_for_participant(db: Session, job_id: int, user: User, allow_eligible_provider: bool = True) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    profile = _provider_profile_for(db, user)
    is_customer = job.customer_id == user.id
    is_assigned_provider = bool(profile and job.provider_id == profile.id)
    has_quote = bool(
        profile
        and job.provider_id in (None, profile.id)
        and db.query(Quote.id).filter(Quote.job_id == job.id, Quote.provider_id == profile.id).first()
    )
    has_invitation = bool(
        profile
        and db.query(JobInvitation.id)
        .filter(JobInvitation.job_id == job.id, JobInvitation.provider_id == profile.id)
        .first()
    )
    can_quote = bool(
        allow_eligible_provider
        and profile
        and job.provider_id is None
        and job.target_provider_id in (None, profile.id)
        and job.status in (JobStatus.REQUESTED, JobStatus.QUOTED)
        and _provider_can_browse_job(db, profile, job)
    )
    if not (is_customer or is_assigned_provider or has_quote or can_quote or has_invitation or user.role == UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to view this job")
    return job


def list_my_jobs(db: Session, user: User):
    query = db.query(Job)
    if user.role == UserRole.CUSTOMER:
        query = query.filter(Job.customer_id == user.id)
    elif user.role == UserRole.PROVIDER:
        profile = _provider_profile_for(db, user)
        if profile is None:
            return []
        quoted_job_ids = db.query(Quote.job_id).filter(Quote.provider_id == profile.id)
        skilled_categories = db.query(ProviderSkill.category_id).filter(ProviderSkill.provider_id == profile.id)
        query = query.filter(
            Job.category_id.in_(skilled_categories),
            or_(
                Job.provider_id == profile.id,
                (Job.id.in_(quoted_job_ids) & Job.status.in_((JobStatus.REQUESTED, JobStatus.QUOTED))),
                Job.target_provider_id == profile.id,
            )
        )
    return query.order_by(Job.created_at.desc(), Job.id.desc()).all()


def list_available_jobs(db: Session, user: User):
    if user.role == UserRole.ADMIN:
        return (
            db.query(Job)
            .filter(
                Job.provider_id.is_(None),
                Job.status.in_((JobStatus.REQUESTED, JobStatus.QUOTED)),
            )
            .order_by(Job.created_at.desc(), Job.id.desc())
            .all()
        )
    profile = _provider_profile_for(db, user)
    if profile is None:
        return []
    quoted_job_ids = db.query(Quote.job_id).filter(Quote.provider_id == profile.id)
    skilled_categories = db.query(ProviderSkill.category_id).filter(ProviderSkill.provider_id == profile.id)
    return (
        db.query(Job)
        .filter(
            Job.provider_id.is_(None),
            or_(Job.target_provider_id.is_(None), Job.target_provider_id == profile.id),
            Job.status.in_((JobStatus.REQUESTED, JobStatus.QUOTED)),
            Job.category_id.in_(skilled_categories),
            ~Job.id.in_(quoted_job_ids),
        )
        .order_by(Job.created_at.desc(), Job.id.desc())
        .all()
    )


def add_quote(db: Session, job_id: int, provider_user: User, payload: QuoteCreate) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status not in (JobStatus.REQUESTED, JobStatus.QUOTED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This job is no longer accepting quotes")

    profile = _provider_profile_for(db, provider_user)
    if profile is None or not _provider_can_quote(db, profile, job):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An available provider with the matching skill must submit identity documents before quoting",
        )
    if job.provider_id is not None and job.provider_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This job is assigned to another provider")
    if job.target_provider_id is not None and job.target_provider_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This job was requested from another provider")

    existing = db.query(Quote).filter(Quote.job_id == job.id, Quote.provider_id == profile.id).first()
    if existing is None:
        db.add(Quote(job_id=job.id, provider_id=profile.id, quoted_amount=payload.quoted_amount))
    else:
        existing.quoted_amount = payload.quoted_amount

    if job.status == JobStatus.REQUESTED:
        try:
            validate_transition(job.status, JobStatus.QUOTED, provider_user.role)
        except InvalidTransitionError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        job.status = JobStatus.QUOTED

    db.commit()
    db.refresh(job)
    return job


def accept_quote(db: Session, job_id: int, quote_id: int, customer: User) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.customer_id != customer.id and customer.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your job")
    if job.status != JobStatus.QUOTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This job has no quote awaiting acceptance")

    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.job_id == job.id).first()
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found for this job")

    try:
        validate_transition(job.status, JobStatus.ACCEPTED, customer.role)
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    job.provider_id = quote.provider_id
    job.quoted_amount = quote.quoted_amount
    job.status = JobStatus.ACCEPTED
    db.commit()
    db.refresh(job)
    return job


def update_status(db: Session, job_id: int, actor: User, payload: JobStatusUpdate) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    profile = _provider_profile_for(db, actor)
    is_customer = job.customer_id == actor.id
    is_assigned_provider = bool(profile and job.provider_id == profile.id)
    if not (is_customer or is_assigned_provider or actor.role == UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a participant on this job")

    if payload.status == JobStatus.ACCEPTED:
        if actor.role not in (UserRole.CUSTOMER, UserRole.ADMIN) or not is_customer:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the job owner can accept a quote")
        if job.provider_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select a quote to accept")
        quote = db.query(Quote).filter(Quote.job_id == job.id, Quote.provider_id == job.provider_id).first()
        if quote is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The assigned provider must submit a quote first")
        job.quoted_amount = quote.quoted_amount

    if payload.status == JobStatus.COMPLETED and actor.role == UserRole.PROVIDER:
        if not is_assigned_provider:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the assigned provider can request completion")
        if payload.final_amount is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="final_amount is required to request completion")
        if job.completion_requested:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Completion is already awaiting customer confirmation")
        try:
            validate_transition(job.status, payload.status, actor.role)
        except InvalidTransitionError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        job.final_amount = payload.final_amount
        job.completion_requested = True
        db.add(
            Notification(
                user_id=job.customer_id,
                job_id=job.id,
                message=f"Your provider marked job #{job.id} complete. Review the work and confirm completion.",
            )
        )
        db.commit()
        db.refresh(job)
        return job

    if payload.status == JobStatus.COMPLETED and (is_customer or actor.role == UserRole.ADMIN):
        if job.status != JobStatus.IN_PROGRESS or not job.completion_requested:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provider has not requested completion")
        if payload.final_amount is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The customer cannot set the final amount")

        job.status = JobStatus.COMPLETED
        job.completion_requested = False
        if job.provider_id is not None:
            db.flush()
            assigned_profile = (
                db.query(ProviderProfile)
                .filter(ProviderProfile.id == job.provider_id)
                .with_for_update()
                .first()
            )
            if assigned_profile is not None:
                completed_count = (
                    db.query(Job.id)
                    .filter(Job.provider_id == assigned_profile.id, Job.status == JobStatus.COMPLETED)
                    .count()
                )
                if completed_count >= 5:
                    assigned_profile.is_verified = True
                db.add(
                    Notification(
                        user_id=assigned_profile.user_id,
                        job_id=job.id,
                        message=f"The customer confirmed completion of job #{job.id}.",
                    )
                )
        db.commit()
        db.refresh(job)
        return job

    if payload.status != JobStatus.COMPLETED and payload.final_amount is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="final_amount is only valid when completing a job")
    if payload.status == JobStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the job owner can confirm job completion")

    try:
        validate_transition(job.status, payload.status, actor.role)
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    job.status = payload.status
    if payload.status == JobStatus.EN_ROUTE:
        db.add(
            Notification(
                user_id=job.customer_id,
                job_id=job.id,
                message=f"Your provider is on the way to job #{job.id}.",
            )
        )
    db.commit()
    db.refresh(job)
    return job
