from typing import List

from fastapi import APIRouter, Depends, HTTPException, status  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session  # pyright: ignore[reportMissingImports]

from app.database.models.notification import Notification
from app.database.models.user import User, UserRole
from app.database.session import get_db
from app.dependencies.auth import get_current_user, require_role
from app.schemas.notification import NotificationAdminOut, NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/mine", response_model=List[NotificationOut])
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .all()
    )


@router.get("/admin/all", response_model=List[NotificationAdminOut])
def get_all_notifications_for_admin(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
):
    return (
        db.query(Notification)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(500)
        .all()
    )


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(Notification.id == notification_id)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Notification.user_id == current_user.id)
    notification = query.first()
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
