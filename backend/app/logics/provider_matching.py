from math import atan2, cos, radians, sin, sqrt
from typing import Optional

from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.models.provider import ProviderProfile, ProviderSkill


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_km = 6371.0
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    value = (
        sin(delta_lat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(delta_lng / 2) ** 2
    )
    value = min(1.0, max(0.0, value))
    return earth_radius_km * 2 * atan2(sqrt(value), sqrt(1 - value))


def find_nearest_available_provider(
    db: Session,
    category_id: int,
    job_lat: Optional[float],
    job_lng: Optional[float],
) -> Optional[ProviderProfile]:
    candidates = (
        db.query(ProviderProfile)
        .join(ProviderSkill, ProviderSkill.provider_id == ProviderProfile.id)
        .filter(
            ProviderSkill.category_id == category_id,
            ProviderProfile.is_available.is_(True),
            ProviderProfile.is_verified.is_(True),
        )
        .order_by(ProviderProfile.rating_avg.desc(), ProviderProfile.rating_count.desc(), ProviderProfile.id.asc())
        .all()
    )
    if not candidates:
        return None
    if job_lat is None or job_lng is None:
        return candidates[0]
    located = [profile for profile in candidates if profile.current_lat is not None and profile.current_lng is not None]
    if not located:
        return candidates[0]
    return min(
        located,
        key=lambda profile: haversine_km(job_lat, job_lng, profile.current_lat, profile.current_lng),
    )
