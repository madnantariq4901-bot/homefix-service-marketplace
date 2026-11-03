from datetime import datetime

from pydantic import BaseModel, ConfigDict  # pyright: ignore[reportMissingImports]


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    message: str
    is_read: bool
    created_at: datetime


class NotificationAdminOut(NotificationOut):
    """Notification with recipient id, exposed only to administrators."""
    user_id: int
