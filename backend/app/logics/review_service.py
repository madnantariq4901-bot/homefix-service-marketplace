from fastapi import HTTPException, status # pyright: ignore[reportMissingImports]
from sqlalchemy.exc import IntegrityError # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.models.job import Job, JobStatus
from app.database.models.provider import ProviderProfile
from app.database.models.review import Review
from app.database.models.user import User
from app.schemas.review import ReviewCreate


def create_review(db: Session, job_id: int, customer: User, payload: ReviewCreate) -> Review:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.customer_id != customer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your job")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job must be completed before reviewing")
    if job.provider_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This job has no assigned provider")
    if db.query(Review).filter(Review.job_id == job_id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job already reviewed")

    review = Review(
        job_id=job.id,
        customer_id=customer.id,
        provider_id=job.provider_id,
        rating=payload.rating,
        comment=payload.comment.strip() if payload.comment else None,
    )
    profile = db.query(ProviderProfile).filter(ProviderProfile.id == job.provider_id).with_for_update().first()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned provider was not found")

    previous_count = profile.rating_count
    profile.rating_count = previous_count + 1
    profile.rating_avg = round(((profile.rating_avg * previous_count) + payload.rating) / profile.rating_count, 2)
    db.add(review)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job already reviewed") from exc
    db.refresh(review)
    return review
