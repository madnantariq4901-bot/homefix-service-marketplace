from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator # pyright: ignore[reportMissingImports]

from app.database.models.job import JobStatus


class JobCreate(BaseModel):
    category_id: int = Field(gt=0)
    preferred_provider_id: Optional[int] = Field(default=None, gt=0)
    description: str = Field(min_length=3, max_length=2000)
    address: str = Field(min_length=3, max_length=500)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)

    @field_validator("description", "address")
    @classmethod
    def trim_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required")
        return value

    @model_validator(mode="after")
    def validate_coordinates(self):
        if (self.lat is None) != (self.lng is None):
            raise ValueError("Latitude and longitude must be provided together")
        return self


class JobStatusUpdate(BaseModel):
    status: JobStatus
    final_amount: Optional[float] = Field(default=None, gt=0, le=100000000)


class JobAdminUpdate(BaseModel):
    category_id: Optional[int] = Field(default=None, gt=0)
    description: Optional[str] = Field(default=None, min_length=3, max_length=2000)
    address: Optional[str] = Field(default=None, min_length=3, max_length=500)
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)

    @field_validator("description", "address")
    @classmethod
    def trim_required_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("This field is required")
        return value

    @model_validator(mode="after")
    def validate_changes(self):
        fields_set = self.model_fields_set
        if not fields_set:
            raise ValueError("At least one job field must be provided")
        for field in ("category_id", "description", "address"):
            if field in fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        if bool({"lat", "lng"} & fields_set) and not {"lat", "lng"}.issubset(fields_set):
            raise ValueError("Latitude and longitude must be provided together")
        if (self.lat is None) != (self.lng is None):
            raise ValueError("Latitude and longitude must both be set or cleared")
        return self


class ProviderApproach(BaseModel):
    provider_id: int = Field(gt=0)


class ProviderApproachOut(BaseModel):
    job_id: int
    provider_id: int
    notification_id: int
    message: str


class JobAttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: str
    media_type: str
    size_bytes: int


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    provider_id: Optional[int] = None
    category_id: int
    description: str
    address: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    status: JobStatus
    quoted_amount: Optional[float] = None
    final_amount: Optional[float] = None
    completion_requested: bool = False
    has_review: bool = False
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    provider_name: Optional[str] = None
    provider_email: Optional[str] = None
    attachments: list[JobAttachmentOut] = Field(default_factory=list)
