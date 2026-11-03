from typing import List

from fastapi.encoders import jsonable_encoder # pyright: ignore[reportMissingImports]
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status # pyright: ignore[reportMissingImports]
from fastapi.responses import FileResponse # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.models.job import Job
from app.database.models.user import User, UserRole
from app.database.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.logics.job_service import MAX_JOB_ATTACHMENTS, MAX_JOB_ATTACHMENT_BYTES, add_job_attachments, add_quote, approach_provider, create_job, delete_job, get_job_attachment, get_job_for_participant, list_available_jobs, list_my_jobs, update_job_details, update_status
from app.logics.job_access import job_response_for_user
from app.logics.connection_manager import manager
from app.logics.job_message_service import create_job_message, list_job_messages
from app.logics.review_service import create_review
from app.schemas.job import JobAdminUpdate, JobAttachmentOut, JobCreate, JobOut, JobStatusUpdate, ProviderApproach, ProviderApproachOut
from app.schemas.job_message import JobMessageCreate, JobMessageOut
from app.schemas.quote import QuoteCreate
from app.schemas.review import ReviewCreate, ReviewOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_response(job: Job, current_user: User) -> JobOut:
    return job_response_for_user(job, current_user)

@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def post_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER, UserRole.ADMIN)),
):
    return _job_response(create_job(db, current_user, payload), current_user)


@router.get("/mine", response_model=List[JobOut])
def get_my_jobs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return [_job_response(job, current_user) for job in list_my_jobs(db, current_user)]


@router.get("/available", response_model=List[JobOut])
def get_available_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVIDER, UserRole.ADMIN)),
):
    return [_job_response(job, current_user) for job in list_available_jobs(db, current_user)]


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _job_response(get_job_for_participant(db, job_id, current_user), current_user)


@router.post("/{job_id}/attachments", response_model=List[JobAttachmentOut], status_code=status.HTTP_201_CREATED)
async def upload_job_attachments(
    job_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if len(files) > MAX_JOB_ATTACHMENTS:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="A job can have at most 5 attachments")
    uploads = []
    for file in files:
        contents = await file.read(MAX_JOB_ATTACHMENT_BYTES + 1)
        uploads.append((file.filename or "attachment", file.content_type or "", contents))
    return add_job_attachments(db, job_id, current_user, uploads)


@router.get("/{job_id}/attachments/{attachment_id}/file")
def get_job_attachment_file(
    job_id: int,
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_job_for_participant(db, job_id, current_user)
    attachment = get_job_attachment(db, job_id, attachment_id)
    return FileResponse(
        attachment.stored_path,
        media_type=attachment.media_type,
        filename=attachment.original_name,
        content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_job(
    job_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
):
    delete_job(db, job_id)


@router.patch("/{job_id}", response_model=JobOut)
def edit_job(
    job_id: int,
    payload: JobAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _job_response(update_job_details(db, job_id, current_user, payload), current_user)


@router.post("/{job_id}/approach", response_model=ProviderApproachOut, status_code=status.HTTP_201_CREATED)
def invite_provider_to_job(
    job_id: int,
    payload: ProviderApproach,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
):
    return approach_provider(db, job_id, payload.provider_id, _admin)


@router.get("/{job_id}/messages", response_model=List[JobMessageOut])
def get_job_messages(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_job_messages(db, job_id, current_user)


@router.post("/{job_id}/messages", response_model=JobMessageOut, status_code=status.HTTP_201_CREATED)
async def post_job_message(
    job_id: int,
    payload: JobMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = create_job_message(db, job_id, current_user, payload)
    await manager.broadcast_to_job(job_id, {"type": "chat_message", "message": jsonable_encoder(message)})
    return message


@router.post("/{job_id}/quote", response_model=JobOut)
def quote_job(
    job_id: int,
    payload: QuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.PROVIDER)),
):
    return _job_response(add_quote(db, job_id, current_user, payload), current_user)


@router.patch("/{job_id}/status", response_model=JobOut)
def patch_job_status(
    job_id: int,
    payload: JobStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _job_response(update_status(db, job_id, current_user, payload), current_user)


@router.post("/{job_id}/review", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def review_job(
    job_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CUSTOMER)),
):
    return create_review(db, job_id, current_user, payload)
