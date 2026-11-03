from pydantic import BaseModel, ConfigDict, Field # pyright: ignore[reportMissingImports]


class QuoteCreate(BaseModel):
    quoted_amount: float = Field(gt=0, le=100000000)


class QuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    provider_id: int
    quoted_amount: float
    provider_name: str
    provider_rating_avg: float
    provider_rating_count: int
