# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.models.user import User
from app.database.session import get_db
from app.schemas.user import UserOut, UserUpdate
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_my_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_my_user(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updates = payload.model_dump(exclude_unset=True)
    if "full_name" in updates and (updates["full_name"] is None or not str(updates["full_name"]).strip()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Full name cannot be empty")
    for field, value in updates.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user