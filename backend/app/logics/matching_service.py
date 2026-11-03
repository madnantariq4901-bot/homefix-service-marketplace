from typing import Optional

from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.models.provider import ProviderProfile
from app.logics.provider_matching import find_nearest_available_provider


def assign_provider_to_job(
    db: Session,
    category_id: int,
    lat: Optional[float],
    lng: Optional[float],
) -> Optional[ProviderProfile]:
    return find_nearest_available_provider(db, category_id, lat, lng)
