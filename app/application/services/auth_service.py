from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import jwt
from app.core.config import settings
from app.core.exceptions import InvalidCredentials, RegistrationError
from app.domain.entities.user import User, UserInDB
from app.infrastructure.persistence.user_repository import UserRepository

# Password Hashing Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def _hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "sub": str(data.get("username"))})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def register_user(self, username: str, password: str) -> User:
        """Creates a new user, hashes password, and returns user with JWT."""
        if self.user_repo.get_user_by_username(username):
            raise RegistrationError("Username already taken.")

        hashed_password = self._hash_password(password)
        user_entity = self.user_repo.create_user(username, hashed_password)
        
        token = self._create_access_token({"username": user_entity.username})
        user_entity.access_token = token
        return user_entity

    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticates user and returns user entity with JWT."""
        # Query for the UserInDB model (which includes the hashed_password)
        db_user = self.user_repo.db.query(UserInDB).filter(UserInDB.username == username).first()
        
        if not db_user or not self._verify_password(password, db_user.hashed_password):
            raise InvalidCredentials()
        
        user_entity = User.model_validate(db_user)
        
        token = self._create_access_token({"username": user_entity.username})
        user_entity.access_token = token
        return user_entity