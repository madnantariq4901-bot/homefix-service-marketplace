from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (UniqueConstraint("job_id", "provider_id", name="uq_quote_job_provider"),)

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("provider_profiles.id"), nullable=False)
    quoted_amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job")
    provider = relationship("ProviderProfile")
