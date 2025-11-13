from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import jwt
from app.core.config import settings
from app.core.exceptions import InvalidCredentials, RegistrationError
from app.domain.entities.user impeor 