from typing import List

from fastapi import APIRouter, Depends, HTTPException, status # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.models.provider import ProviderProfile
from app.database.models.quote import Quote
from app.database.models.user import User, UserRole
from app.database.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.logics.job_service import accept_quote, get_job_for_participant
from app.logics.job_access import job_response_for_user
from app.schemas.job import JobOut
from app.schemas.quote import QuoteOut

router = APIRouter(prefix="/jobs/{job_id}/quotes", tags=["quotes"])


def quote_response(quote: Quote) -> dict:
    return {
        "id": quote.id,
        "job_id": quote.job_id,
        "provider_id": quote.provider_id,
        "quoted_amount": quote.quoted_amount,
        "provider_name": quote.provider.user.full_name,
        "provider_rating_avg": quote.provider.rating_avg,
        "provider_rating_count": quote.provider.rating_count,
    }


@router.get("", response_model=List[QuoteOut])
def list_job_quotes(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = get_job_for_participant(db, job_id, current_user)
    if current_user.role == UserRole.ADMIN or job.customer_id == current_user.id:
        quotes = db.query(Quote).filter(Quote.job_id == job_id).order_by(Quote.created_at.desc(), Quote.id.desc()).all()
        return [quote_response(quote) for quote in quotes]

    profile = db.query(ProviderProfile).filter(ProviderProfile.user_id == current_user.id).first()
    if profile is None or not (job.provider_id == profile.id or db.query(Quote.id).filter(Quote.job_id == job_id, Quote.provider_id == profile.id).first()):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot view quotes for this job")
    quotes = db.query(Quote).filter(Quote.job_id == job_id, Quote.provider_id == profile.id).order_by(Quote.created_at.desc(), Quote.id.desc()).all()
    return [quote_response(quote) for quote in quotes]


@router.post("/{quote_id}/accept", response_model=JobOut)
def accept_job_quote(
    job_id: int,
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER, UserRole.ADMIN)),
):
    job = accept_quote(db, job_id, quote_id, current_user)
    return job_response_for_user(job, current_user)
