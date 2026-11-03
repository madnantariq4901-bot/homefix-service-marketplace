from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, false, func

from app.database.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(String(500), nullable=False)
    is_read = Column(Boolean, default=False, server_default=false(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
