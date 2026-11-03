from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field # pyright: ignore[reportMissingImports]

class SkillCreate(BaseModel):
    category_id: int = Field(gt=0)
    years_experience: int = Field(default=0, ge=0, le=80)


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    years_experience: int


class AvailabilityUpdate(BaseModel):
    is_available: bool


class VerificationUpdate(BaseModel):
    is_verified: bool


class LocationUpdate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class ProviderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    is_verified: bool
    is_available: bool
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    rating_avg: float
    rating_count: int
    identity_documents_submitted: bool = False
    completed_job_count: int = 0
    skills: List[SkillOut] = Field(default_factory=list)


class ProviderDirectoryOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    is_verified: bool
    is_available: bool
    rating_avg: float
    rating_count: int
    completed_job_count: int = 0
    skills: List[SkillOut] = Field(default_factory=list)


class ProviderAdminOut(ProviderDirectoryOut):
    identity_documents_submitted: bool = False


class PublicSkillOut(BaseModel):
    """A skill shown on public pages: the category name instead of a bare id."""

    category_id: int
    category: str
    years_experience: int


class PublicProviderOut(BaseModel):
    """Safe-to-publish provider data (no user_id, email, phone or coordinates)."""

    id: int
    full_name: str
    is_verified: bool
    is_available: bool
    rating_avg: float
    rating_count: int
    completed_job_count: int
    skills: List[PublicSkillOut] = Field(default_factory=list)
