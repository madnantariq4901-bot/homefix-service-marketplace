from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    base_hourly_rate: float = Field(gt=0, le=1000000)
    description: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Service name is required")
        return value


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    base_hourly_rate: Optional[float] = Field(default=None, gt=0, le=1000000)
    description: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = " ".join(value.split())
        if not value:
            raise ValueError("Service name is required")
        return value

    @field_validator("description")
    @classmethod
    def trim_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Description cannot be blank")
        return value

    @model_validator(mode="after")
    def validate_changes(self):
        fields_set = self.model_fields_set
        if not fields_set:
            raise ValueError("At least one service field must be provided")
        if "name" in fields_set and self.name is None:
            raise ValueError("Service name cannot be null")
        if "base_hourly_rate" in fields_set and self.base_hourly_rate is None:
            raise ValueError("Hourly rate cannot be null")
        return self


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_hourly_rate: float
    description: Optional[str] = None
