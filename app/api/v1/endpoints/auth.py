from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.application.services.auth_service import AuthService
from app.infrastructure.persistence.user_repository import UserRepository
from app.domain.entities.user import User

router = APIRouter()

class UserAuth(BaseModel):
    username: str
    password: str

def get_auth_service(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    return AuthService(user_repo)

@router.post("/resigster", response_model = User, status_code = status.HTTP_201_CREATED)
def register_user(
    user_in: UserAuth,
    auth_service: AuthService = Depends(get_auth_service)
):  
    """Register a new user and return the user object with a JWT."""
    return auth_service.register_user(user_in.username, user_in.password)

@router.post("/login", response_model = User)
def login_user(
    user_in: UserAuth,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Log in an existing user and return the user object with a JWT."""
    return auth_service.authenticate_user(user_in.username, user_in.password) 