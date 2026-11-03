from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]
from fastapi import HTTPException, status # pyright: ignore[reportMissingImports]

from app.database.models.user import User


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user