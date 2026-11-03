from typing import List
from fastapi import APIRouter, Depends, status # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session   # pyright: ignore[reportMissingImports]

from app.database.session import get_db
from app.database.models.user import UserRole
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.dependencies.auth import require_role
from app.logics.category_service import delete_category, list_categories, create_category, update_category

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=List[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return list_categories(db)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def add_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    return create_category(db, payload)


@router.patch("/{category_id}", response_model=CategoryOut)
def edit_category(
    category_id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    return update_category(db, category_id, payload)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_category(
    category_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    delete_category(db, category_id)