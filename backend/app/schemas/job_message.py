from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class JobMessageCreate(BaseModel):
    body: Optional[str] = Field(default=None, max_length=2000)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)

    @field_validator("body")
    @classmethod
    def trim_body(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_message_kind(self):
        has_body = self.body is not None
        has_latitude = self.latitude is not None
        has_longitude = self.longitude is not None
        has_location = has_latitude and has_longitude
        if has_latitude != has_longitude:
            raise ValueError("Latitude and longitude must be provided together")
        if has_body == has_location:
            raise ValueError("Provide either message text or a location")
        return self


class JobMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    sender_id: int
    sender_name: str
    body: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime