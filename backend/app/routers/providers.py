from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.models.provider import ProviderProfile
from app.database.models.user import User, UserRole
from app.database.session import get_db
from app.dependencies.auth import require_role
from app.logics.provider_service import (
    add_skill,
    completed_job_counts,
    get_or_create_profile,
    get_public_provider,
    list_public_providers,
    provider_profile_response,
    save_identity_documents,
    update_availability,
    update_location,
)
from app.schemas.provider import (
    AvailabilityUpdate,
    LocationUpdate,
    ProviderAdminOut,
    ProviderDirectoryOut,
    ProviderOut,
    PublicProviderOut,
    SkillCreate,
    SkillOut,
    VerificationUpdate,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=List[ProviderAdminOut])
def list_providers(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
):
    profiles = db.query(ProviderProfile).order_by(ProviderProfile.id.asc()).all()
    job_counts = completed_job_counts(db, [profile.id for profile in profiles])
    return [
        {
            "id": profile.id,
            "user_id": profile.user_id,
            "full_name": profile.user.full_name,
            "is_verified": profile.is_verified,
            "is_available": profile.is_available,
            "rating_avg": profile.rating_avg,
            "rating_count": profile.rating_count,
            "completed_job_count": job_counts[profile.id],
            "identity_documents_submitted": profile.identity_documents_submitted,
            "skills": profile.skills,
        }
        for profile in profiles
    ]


@router.get("/public", response_model=List[PublicProviderOut])
def list_public(
    category: Optional[str] = None,
    available_only: bool = False,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None, max_length=120),
    sort_by: Literal["recommended", "completed_jobs", "rating", "experience", "name"] = "recommended",
    db: Session = Depends(get_db),
):
    """Public directory: verified providers only. Declared before /{provider_id}."""
    return list_public_providers(
        db,
        category=category,
        available_only=available_only,
        limit=limit,
        offset=offset,
        search=search.strip() if search else None,
        sort_by=sort_by,
    )


@router.get("/public/{provider_id}", response_model=PublicProviderOut)
def get_public(provider_id: int, db: Session = Depends(get_db)):
    return get_public_provider(db, provider_id)


@router.get("/me", response_model=ProviderOut)
def read_my_profile(db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.PROVIDER))):
    return provider_profile_response(db, get_or_create_profile(db, current_user))


@router.post("/me/identity", response_model=ProviderOut)
async def upload_my_identity(
    id_front: UploadFile = File(...),
    id_back: UploadFile = File(...),
    selfie: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVIDER)),
):
    image_limit = 5 * 1024 * 1024
    contents = []
    for upload in (id_front, id_back, selfie):
        contents.append(await upload.read(image_limit + 1))
    return save_identity_documents(db, current_user, *contents)


@router.get("/{provider_id}", response_model=PublicProviderOut)
def get_provider_details(provider_id: int, db: Session = Depends(get_db)):
    """Compatibility route that exposes only the same safe data as public profiles."""
    return get_public_provider(db, provider_id)


@router.post("/me/skills", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def add_my_skill(payload: SkillCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.PROVIDER))):
    return add_skill(db, current_user, payload)


@router.patch("/me/availability", response_model=ProviderOut)
def set_my_availability(payload: AvailabilityUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.PROVIDER))):
    return provider_profile_response(db, update_availability(db, current_user, payload))


@router.patch("/me/location", response_model=ProviderOut)
def set_my_location(payload: LocationUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role(UserRole.PROVIDER))):
    return provider_profile_response(db, update_location(db, current_user, payload))


@router.patch("/{provider_id}/verification", response_model=ProviderOut)
def set_provider_verification(
    provider_id: int,
    payload: VerificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    profile = db.query(ProviderProfile).filter(ProviderProfile.id == provider_id).first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    profile.is_verified = payload.is_verified
    db.commit()
    db.refresh(profile)
    return provider_profile_response(db, profile)
