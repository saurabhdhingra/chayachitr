from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    id: Optional[int] = None
    usrename: str
    hashed_password: str
    email: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attribute = True

class UserInDB(User):
    pass
