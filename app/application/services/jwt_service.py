import jwt
from datetime import datetime, timedelta
import os
from typing import Union # Imported to support type hints for Python < 3.10

# JWT settings (should ideally come from config/env)
SECRET_KEY = os.getenv("SECRET_KEY", "YOUR_SECURE_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class JWTService:
    """Handles the creation and decoding of JSON Web Tokens."""

    def __init__(self):
        # Service initialization, can load configurations here if needed
        pass

    def create_access_token(self, data: dict, expires_delta: timedelta = None) -> str:
        """Creates a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            # Use the default expiration time
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Add expiry and token type subject
        to_encode.update({"exp": expire, "sub": "access"})
        
        # Encode the token using the secret key and algorithm
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> Union[dict, None]:
        """Decodes and validates a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            print("Token expired.")
            return None 
        except jwt.InvalidTokenError:
            print("Invalid token provided.")
            return None