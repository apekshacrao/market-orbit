from uuid import uuid4

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.security import get_password_hash
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
    def authenticate(login_data):
        # Starter auth stub
        return {"access_token": "mock_token", "token_type": "bearer"}