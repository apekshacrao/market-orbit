from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db.models.user import User


class AuthService:

    @staticmethod
    def register(user_in, db: Session):
        existing_user = db.query(User).filter(User.email == user_in.email).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            id=str(uuid4()),
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.name,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def authenticate(login_data, db: Session):
        user = db.query(User).filter(User.email == login_data.email).first()

        if not user or not verify_password(
            login_data.password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token(subject=user.id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }
