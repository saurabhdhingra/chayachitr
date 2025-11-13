from pydantic import BaseModel, Field
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: Optional[int] = None
    is_active: bool = True
    
    access_token: Optional[str] = Field(None, alias="token") 
    
    class Config:
        from_attributes = True 
        populate_by_name = True

class UserInDB(User):
    hashed_password: str