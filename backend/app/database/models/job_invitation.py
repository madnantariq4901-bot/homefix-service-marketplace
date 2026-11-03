from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, func

from app.database.base import Base


class JobInvitation(Base):
    __tablename__ = "job_invitations"
    __table_args__ = (UniqueConstraint("job_id", "provider_id", name="uq_job_invitation_provider"),)

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)