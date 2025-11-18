from passlib.context import CryptContext
from fastapi import HTTPException, status
from datetime import timedelta # Keep for token expiration calculation if needed later

# Import the SQLAlchemy ORM Model (Assuming this is correct from previous step)
from app.infrastructure.database.models import UserDB 
# Assuming UserDB is the ORM model defined elsewhere

# Configuration for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Handles authentication and authorization business logic."""
    # Now correctly requires two dependencies
    def __init__(self, user_repo, jwt_service):
        self.user_repo = user_repo
        self.jwt_service = jwt_service # Storing the injected JWT Service

    # --- Utility Methods ---

    def _hash_password(self, password: str) -> str:
        """Hashes the provided password."""
        password_bytes = password.encode('utf-8')
        return pwd_context.hash(password_bytes[:72])

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain password against a hashed one."""
        return pwd_context.verify(plain_password, hashed_password)

    # --- Business Logic Methods ---
    
    def register_user(self, username: str, password: str) -> dict:
        """Registers a new user in the database."""
        
        # 1. Check if user already exists
        if self.user_repo.db.query(UserDB).filter(UserDB.username == username).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, 
                detail="Username already registered"
            )

        # 2. Hash the password
        hashed_password = self._hash_password(password)

        # 3. Create the new user ORM object
        new_user = UserDB(
            username=username,
            hashed_password=hashed_password
        )
        
        # 4. Save to database
        self.user_repo.db.add(new_user)
        self.user_repo.db.commit()
        self.user_repo.db.refresh(new_user)
        
        return {"message": "User registered successfully"}

    def authenticate_user(self, username: str, password: str) -> dict:
        """Authenticates user credentials and returns a JWT token."""
        
        # 1. Retrieve the user from the database
        db_user = self.user_repo.db.query(UserDB).filter(UserDB.username == username).first()

        # 2. Verify existence and password
        if not db_user or not self._verify_password(password, db_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Create the access token - DELEGATE TO JWT SERVICE
        # The JWTService handles the expiry and encoding logic internally
        access_token = self.jwt_service.create_access_token(data={"sub": db_user.username})

        return {"access_token": access_token, "token_type": "bearer"}