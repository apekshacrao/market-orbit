from fastapi import Depends, HTTPException, status
from app.db.session import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user():
    # Starter auth dependency stub
    return {"id": "user-1", "email": "demo@example.com", "name": "Demo User", "is_active": True}
