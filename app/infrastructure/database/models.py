from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key = True, index = True)
    username = Column(String, unique = True, index = True, nullable = False)
    hashed_password = Column(String, nullable = False)
    is_active = Column(Boolean, default = True)
    
    images = relationship("ImageDB", back_populates = "owner")

class ImageDB(Base):
    __tablename__ = "images"

    id = Column(String, primary_key = True, index = True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String, nullable = False)
    storage_url = Column(String, nullable = False)
    mimetype = Column(String)
    size_bytes = Column(JSON)
    metadata = Column(JSON)
    is_transformed = Column(Boolean, default = False)

    owner = relationship("UserDB", back_populates = "images")