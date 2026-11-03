import enum
from sqlalchemy import Column, Integer, String, Float
from app.database.base import Base


class CategoryName(str, enum.Enum):
    PLUMBER = "plumber"
    ELECTRICIAN = "electrician"
    CARPENTER = "carpenter"
    MECHANIC = "mechanic"
    AC_TECHNICIAN = "ac_technician"
    PAINTER = "painter"
    CLEANER = "cleaner"
    MASON = "mason"


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False)
    base_hourly_rate = Column(Float, nullable=False)
    description = Column(String, nullable=True)