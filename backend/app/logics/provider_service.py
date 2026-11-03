import logging
import os
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, or_ # pyright: ignore[reportMissingImports]
from fastapi import HTTPException, status # pyright: ignore[reportMissingImports]
from sqlalchemy.exc import SQLAlchemyError # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session, selectinload # pyright: ignore[reportMissingImports]

from app.config import settings
from app.database.models.category import ServiceCategory
from app.database.models.job import Job, JobStatus
from app.database.models.provider import ProviderProfile, ProviderSkill
from app.database.models.user import User
from app.schemas.provider import AvailabilityUpdate, LocationUpdate, SkillCreate

logger = logging.getLogger(__name__)
MAX_IDENTITY_IMAGE_BYTES = 5 * 1024 * 1024


def _image_extension(contents: bytes) -> str:
    if contents.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Identity images must be JPEG or PNG files",
    )


def _store_identity_image(contents: bytes) -> str:
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identity images cannot be empty")
    if len(contents) > MAX_IDENTITY_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Each identity image must be 5 MB or smaller")

    extension = _image_extension(contents)
    directory = settings.IDENTITY_UPLOAD_DIR
    path = directory / f"{uuid4().hex}{extension}"
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(directory, 0o700)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as image_file:
            image_file.write(contents)
    except OSError as exc:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            logger.exception("Unable to remove a partially written provider identity image")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to securely store identity images") from exc
    return str(path)


def _remove_identity_files(paths: list[str]) -> None:
    for path in paths:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            logger.exception("Unable to remove an uncommitted provider identity image")


def _completed_job_count(db: Session, provider_id: int) -> int:
    return db.query(Job.id).filter(
        Job.provider_id == provider_id,
        Job.status == JobStatus.COMPLETED,
    ).count()


def completed_job_counts(db: Session, provider_ids: list[int]) -> dict[int, int]:
    counts = {provider_id: 0 for provider_id in provider_ids}
    if not provider_ids:
        return counts
    rows = (
        db.query(Job.provider_id, func.count(Job.id))
        .filter(Job.provider_id.in_(provider_ids), Job.status == JobStatus.COMPLETED)
        .group_by(Job.provider_id)
        .all()
    )
    counts.update({provider_id: count for provider_id, count in rows})
    return counts


def provider_profile_response(db: Session, profile: ProviderProfile) -> dict:
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "is_verified": profile.is_verified,
        "is_available": profile.is_available,
        "current_lat": profile.current_lat,
        "current_lng": profile.current_lng,
        "rating_avg": profile.rating_avg,
        "rating_count": profile.rating_count,
        "identity_documents_submitted": profile.identity_documents_submitted,
        "completed_job_count": _completed_job_count(db, profile.id),
        "skills": profile.skills,
    }


def save_identity_documents(
    db: Session,
    current_user: User,
    id_front: bytes,
    id_back: bytes,
    selfie: bytes,
) -> dict:
    profile = get_or_create_profile(db, current_user)
    if profile.identity_documents_submitted:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Identity documents have already been submitted")

    stored_paths: list[str] = []
    try:
        for contents in (id_front, id_back, selfie):
            stored_paths.append(_store_identity_image(contents))
    except HTTPException:
        _remove_identity_files(stored_paths)
        raise

    profile.identity_front_path, profile.identity_back_path, profile.identity_selfie_path = stored_paths
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        _remove_identity_files(stored_paths)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to save identity documents") from exc
    db.refresh(profile)
    return provider_profile_response(db, profile)

def get_or_create_profile(db: Session, current_user: User) -> ProviderProfile:
    profile = db.query(ProviderProfile).filter(ProviderProfile.user_id == current_user.id).first()
    if profile is not None:
        return profile

    profile = ProviderProfile(user_id=current_user.id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def add_skill(db: Session, current_user: User, payload: SkillCreate) -> ProviderSkill:
    category = db.query(ServiceCategory).filter(ServiceCategory.id == payload.category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    profile = get_or_create_profile(db, current_user)

    existing = (
        db.query(ProviderSkill)
        .filter(ProviderSkill.provider_id == profile.id, ProviderSkill.category_id == payload.category_id)
        .first()
    )
    if existing is not None:
        existing.years_experience = payload.years_experience
        db.commit()
        db.refresh(existing)
        return existing

    skill = ProviderSkill(
        provider_id=profile.id,
        category_id=payload.category_id,
        years_experience=payload.years_experience,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


def update_availability(db: Session, current_user: User, payload: AvailabilityUpdate) -> ProviderProfile:
    profile = get_or_create_profile(db, current_user)
    profile.is_available = payload.is_available
    db.commit()
    db.refresh(profile)
    return profile


def update_location(db: Session, current_user: User, payload: LocationUpdate) -> ProviderProfile:
    profile = get_or_create_profile(db, current_user)
    profile.current_lat = payload.lat
    profile.current_lng = payload.lng
    db.commit()
    db.refresh(profile)
    return profile


def _to_public(profile: ProviderProfile) -> dict:
    return {
        "id": profile.id,
        "full_name": profile.user.full_name,
        "is_available": profile.is_available,
        "rating_avg": profile.rating_avg,
        "rating_count": profile.rating_count,
        "skills": [
            {
                "category_id": skill.category_id,
                "category": skill.category.name,
                "years_experience": skill.years_experience,
            }
            for skill in profile.skills
        ],
    }


def _public_query(db: Session):
    return (
        db.query(ProviderProfile)
        .options(
            selectinload(ProviderProfile.user),
            selectinload(ProviderProfile.skills).selectinload(ProviderSkill.category),
        )
        .filter(ProviderProfile.is_verified.is_(True))
    )


def list_public_providers(
    db: Session,
    category: str | None = None,
    available_only: bool = False,
    limit: int = 20,
    offset: int = 0,
    search: str | None = None,
    sort_by: str = "recommended",
) -> list[dict]:
    """Return verified providers, recommended by completed jobs and ratings."""
    query = _public_query(db)
    if available_only:
        query = query.filter(ProviderProfile.is_available.is_(True))
    if category is not None:
        query = query.filter(
            ProviderProfile.skills.any(ProviderSkill.category.has(ServiceCategory.name == category))
        )
    if search:
        term = f"%{search.strip()}%"
        service_name = func.replace(func.lower(ServiceCategory.name), "_", " ")
        query = query.filter(
            or_(
                ProviderProfile.user.has(User.full_name.ilike(term)),
                ProviderProfile.skills.any(ProviderSkill.category.has(service_name.ilike(term))),
            )
        )

    completed_count = (
        db.query(func.count(Job.id))
        .filter(Job.provider_id == ProviderProfile.id, Job.status == JobStatus.COMPLETED)
        .correlate(ProviderProfile)
        .scalar_subquery()
    )

    if sort_by == "name":
        query = query.join(ProviderProfile.user).order_by(User.full_name.asc(), ProviderProfile.id.asc())
    elif sort_by == "experience":
        experience_query = (
            db.query(func.max(ProviderSkill.years_experience))
            .filter(ProviderSkill.provider_id == ProviderProfile.id)
        )
        if category is not None:
            experience_query = experience_query.filter(
                ProviderSkill.category.has(ServiceCategory.name == category)
            )
        max_experience = experience_query.correlate(ProviderProfile).scalar_subquery()
        query = query.order_by(
            max_experience.desc().nullslast(),
            ProviderProfile.rating_avg.desc(),
            ProviderProfile.rating_count.desc(),
            ProviderProfile.id.asc(),
        )
    elif sort_by == "rating":
        query = query.order_by(
            ProviderProfile.rating_avg.desc(),
            ProviderProfile.rating_count.desc(),
            ProviderProfile.id.asc(),
        )
    elif sort_by == "completed_jobs":
        query = query.order_by(completed_count.desc(), ProviderProfile.rating_avg.desc(), ProviderProfile.id.asc())
    else:
        query = query.order_by(
            completed_count.desc(),
            ProviderProfile.rating_avg.desc(),
            ProviderProfile.rating_count.desc(),
            ProviderProfile.id.asc(),
        )

    profiles = query.limit(limit).offset(offset).all()
    job_counts = completed_job_counts(db, [profile.id for profile in profiles])
    return [
        {
            **_to_public(profile),
            "is_verified": profile.is_verified,
            "completed_job_count": job_counts[profile.id],
        }
        for profile in profiles
    ]


def get_public_provider(db: Session, provider_id: int) -> dict:
    profile = _public_query(db).filter(ProviderProfile.id == provider_id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return {
        **_to_public(profile),
        "is_verified": profile.is_verified,
        "completed_job_count": _completed_job_count(db, profile.id),
    }
