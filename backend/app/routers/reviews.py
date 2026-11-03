# app/routers/reviews.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.session import get_db
from app.database.models.provider import ProviderProfile
from app.database.models.review import Review
from app.schemas.review import ReviewOut

router = APIRouter(prefix="/providers", tags=["reviews"])


@router.get("/{provider_id}/reviews", response_model=List[ReviewOut])
def list_provider_reviews(provider_id: int, db: Session = Depends(get_db)):
    profile = db.query(ProviderProfile).filter(ProviderProfile.id == provider_id).first()
    if profile is None or not profile.is_verified:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return db.query(Review).filter(Review.provider_id == provider_id).order_by(Review.created_at.desc()).all()