import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.model import User


class AuthRepository:
    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.scalar(
            select(User).where(User.email == email)
        )

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
        return db.get(User, user_id)

    @staticmethod
    def create_user(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user