from sqlalchemy.orm import Session
from app.infrastructure.database.models import UserDB
from app.domain.entities.user import UserCreate, User

class UserRepository: 
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_username(self, username: str) -> User | None:
        db_user = self.db.query(UserDB).filter(UserDB.username == username).first()

        if db_user : 
            return User.model_validate(db_user)
        return None

    def create_user(self, username: str, hashed_password: str) -> User:
        db_user = UserDB(username = username, hashed_password = hashed_password)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return User.model_validate(db_user)