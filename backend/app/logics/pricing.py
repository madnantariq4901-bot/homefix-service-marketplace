from app.config import settings
from app.models import ServiceCategory


def estimate_starting_price(category: ServiceCategory, estimated_hours: float = 1.0) -> float:
    return round(settings.CALLOUT_FEE + category.base_hourly_rate * estimated_hours, 2)