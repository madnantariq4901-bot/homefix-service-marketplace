from fastapi import APIRouter, Depends, status # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]

from app.database.session import get_db
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import LoginRequest, PasswordResetConfirm, PasswordResetRequest, TokenResponse
from app.logics.auth_service import authenticate_user, request_password_reset, reset_password, signup_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    return signup_user(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    token = authenticate_user(db, payload.email, payload.password)
    return TokenResponse(access_token=token)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    request_password_reset(db, str(payload.email))
    return {"message": "If an account exists for this email, a password reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    reset_password(db, payload.token, payload.new_password)
    return {"message": "Password has been reset. You can now sign in."}