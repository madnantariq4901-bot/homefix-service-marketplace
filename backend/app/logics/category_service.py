from typing import List
from sqlalchemy import func # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]
from fastapi import HTTPException, status # pyright: ignore[reportMissingImports]

from app.database.models.category import ServiceCategory
from app.database.models.job import Job
from app.schemas.category import CategoryCreate, CategoryUpdate


def list_categories(db: Session) -> List[ServiceCategory]:
    return db.query(ServiceCategory).all()


def create_category(db: Session, payload: CategoryCreate) -> ServiceCategory:
    existing = db.query(ServiceCategory).filter(func.lower(ServiceCategory.name) == payload.name.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category already exists")

    category = ServiceCategory(
        name=payload.name,
        base_hourly_rate=payload.base_hourly_rate,
        description=payload.description,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, payload: CategoryUpdate) -> ServiceCategory:
    category = db.query(ServiceCategory).filter(ServiceCategory.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    changes = payload.model_dump(exclude_unset=True)
    if "name" in changes:
        duplicate = (
            db.query(ServiceCategory)
            .filter(
                func.lower(ServiceCategory.name) == changes["name"].lower(),
                ServiceCategory.id != category_id,
            )
            .first()
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service already exists")
    for field, value in changes.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = db.query(ServiceCategory).filter(ServiceCategory.id == category_id).first()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if db.query(Job.id).filter(Job.category_id == category_id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This service has jobs and cannot be deleted",
        )

    db.delete(category)
    db.commit()