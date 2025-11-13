from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.config import settings
from app.application.services.auth_service import auth_service
from app.domain.entities.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "api/v1/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Decodes the JWT token and fetches the corresponding user.
    """
    cresdentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED, 
        detail = "Could not validate credentials", 
        headers = {"WWW-Authenticate": "Bearer"},
    )

    try: 
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise cresdentials_exception
    
    except JWTError:
        raise cresdentials_exception

    auth_service = AuthService()
    user = auth_service.get_user_by_username(username = username)

    if user is None:
        raise cresdentials_exception
    
    return user