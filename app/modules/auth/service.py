from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.modules.auth.model import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schema import TokenResponse, UserRegisterRequest


class AuthService:
    @staticmethod
    def register_student(
        db: Session,
        payload: UserRegisterRequest,
    ) -> User:
        email = str(payload.email).strip().lower()

        existing_user = AuthRepository.get_by_email(db, email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        user = User(
            full_name=payload.full_name.strip(),
            email=email,
            hashed_password=hash_password(payload.password),
            role="student",
            preferred_language=payload.preferred_language,
        )

        return AuthRepository.create_user(db, user)

    @staticmethod
    def login(
        db: Session,
        email: str,
        password: str,
    ) -> TokenResponse:
        normalized_email = email.strip().lower()
        user = AuthRepository.get_by_email(db, normalized_email)

        if not user:
            verify_password(password, DUMMY_HASH)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive",
            )

        token = create_access_token(str(user.id))

        return TokenResponse(access_token=token)