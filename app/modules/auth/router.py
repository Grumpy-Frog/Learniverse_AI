from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.model import User
from app.modules.auth.schema import (
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.modules.auth.service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserRegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    return AuthService.register_student(db, payload)


@router.post(
    "/token",
    response_model=TokenResponse,
)
def login_for_swagger(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    return AuthService.login(
        db=db,
        email=form_data.username,
        password=form_data.password,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user