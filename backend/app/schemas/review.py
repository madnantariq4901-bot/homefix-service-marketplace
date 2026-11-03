from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator # pyright: ignore[reportMissingImports]


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("comment")
    @classmethod
    def clean_comment(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    provider_id: int
    rating: int
    comment: Optional[str] = None
