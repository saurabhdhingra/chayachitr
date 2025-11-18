from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import InvalidCredentials, UserNotFound
from app.core.database import get_db
from app.domain.entities.user import User
from app.infrastructure.persistence.user_repository import UserRepository # Needed for DB lookup

# This scheme will be used for dependency injection in protected endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login")

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency provider for the User Repository."""
    return UserRepository(db=db)

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    """
    Decodes the JWT token, validates it, and fetches the corresponding User entity.
    """
    try:
        # Decode the JWT payload
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        
        if username is None:
            raise InvalidCredentials(detail="Invalid authentication token payload.")
            
    except JWTError:
        # JWT token is malformed, expired, or signature is invalid
        raise InvalidCredentials(detail="Invalid or expired token.")

    # Fetch user from the database
    user = user_repo.get_user_by_username(username=username)

    if user is None:
        raise UserNotFound(detail="Token user not found in database.")
        
    return user