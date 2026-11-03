import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, false, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class JobStatus(str, enum.Enum):
    REQUESTED = "requested"
    QUOTED = "quoted"
    ACCEPTED = "accepted"
    EN_ROUTE = "en_route"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("provider_profiles.id"), nullable=True)
    target_provider_id = Column(Integer, ForeignKey("provider_profiles.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    description = Column(String, nullable=False)
    address = Column(String, nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.REQUESTED, nullable=False)
    quoted_amount = Column(Float, nullable=True)
    final_amount = Column(Float, nullable=True)
    completion_requested = Column(Boolean, default=False, server_default=false(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    customer = relationship("User", foreign_keys=[customer_id])
    provider = relationship("ProviderProfile", foreign_keys=[provider_id])
    target_provider = relationship("ProviderProfile", foreign_keys=[target_provider_id])
    category = relationship("ServiceCategory")
    review = relationship("Review", uselist=False, back_populates="job")
    attachments = relationship("JobAttachment", back_populates="job", cascade="all, delete-orphan")
