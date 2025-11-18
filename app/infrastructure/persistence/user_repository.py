from sqlalchemy.orm import Session
from app.infrastructure.database.models import UserDB
from app.domain.entities.user import UserCreate, User
from typing import Optional # NEW: Import Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    # FIX: Changed 'User | None' to 'Optional[User]' for Python < 3.10 compatibility
    def get_user_by_username(self, username: str) -> Optional[User]:
        db_user = self.db.query(UserDB).filter(UserDB.username == username).first()
        if db_user:
            return User.model_validate(db_user)
        return None

    def create_user(self, username: str, hashed_password: str) -> User:
        db_user = UserDB(username=username, hashed_password=hashed_password)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return User.model_validate(db_user)