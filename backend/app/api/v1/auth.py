from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user, get_db

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db=Depends(get_db)):
    return AuthService.register(user_in, db)

@router.post("/login", response_model=Token)
def login(login_data: UserLogin):
    return AuthService.authenticate(login_data)

@router.get("/me", response_model=UserResponse)
def get_me(current_user = Depends(get_current_user)):
    return current_user
