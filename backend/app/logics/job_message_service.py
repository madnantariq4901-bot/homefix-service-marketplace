from fastapi import HTTPException, status # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session, joinedload # pyright: ignore[reportMissingImports]

from app.database.models.job import Job
from app.database.models.job_message import JobMessage
from app.database.models.provider import ProviderProfile
from app.database.models.user import User, UserRole
from app.schemas.job_message import JobMessageCreate


def get_chat_job(db: Session, job_id: int, actor: User) -> Job:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    profile = None
    if actor.role == UserRole.PROVIDER:
        profile = db.query(ProviderProfile).filter(ProviderProfile.user_id == actor.id).first()
    if job.customer_id != actor.id and not (profile and job.provider_id == profile.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only job participants can access chat")
    return job


def _message_out(message: JobMessage) -> dict:
    return {
        "id": message.id,
        "job_id": message.job_id,
        "sender_id": message.sender_id,
        "sender_name": message.sender.full_name,
        "body": message.body,
        "latitude": message.latitude,
        "longitude": message.longitude,
        "created_at": message.created_at,
    }


def list_job_messages(db: Session, job_id: int, actor: User) -> list[dict]:
    get_chat_job(db, job_id, actor)
    messages = (
        db.query(JobMessage)
        .options(joinedload(JobMessage.sender))
        .filter(JobMessage.job_id == job_id)
        .order_by(JobMessage.created_at.desc(), JobMessage.id.desc())
        .limit(100)
        .all()
    )
    return [_message_out(message) for message in reversed(messages)]


def create_job_message(db: Session, job_id: int, actor: User, payload: JobMessageCreate) -> dict:
    get_chat_job(db, job_id, actor)
    message = JobMessage(
        job_id=job_id,
        sender_id=actor.id,
        body=payload.body,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return _message_out(message)