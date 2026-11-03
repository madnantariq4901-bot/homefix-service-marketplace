from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database.base import Base


class ProviderProfile(Base):
    __tablename__ = "provider_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_available = Column(Boolean, default=False, nullable=False)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    rating_avg = Column(Float, default=0.0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    identity_front_path = Column(String, nullable=True)
    identity_back_path = Column(String, nullable=True)
    identity_selfie_path = Column(String, nullable=True)

    user = relationship("User")
    skills = relationship("ProviderSkill", back_populates="provider", cascade="all, delete-orphan")

    @property
    def identity_documents_submitted(self) -> bool:
        return bool(self.identity_front_path and self.identity_back_path and self.identity_selfie_path)


class ProviderSkill(Base):
    __tablename__ = "provider_skills"
    __table_args__ = (UniqueConstraint("provider_id", "category_id", name="uq_provider_category"),)

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("provider_profiles.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("service_categories.id"), nullable=False)
    years_experience = Column(Integer, default=0, nullable=False)

    provider = relationship("ProviderProfile", back_populates="skills")
    category = relationship("ServiceCategory")
