from sqlalchemy.orm import Session
from sqlalchemy import func
from app.infrastructure.database.models import ImageDB
from app.domain.entities.image import image
from typing import List, Dict, Any

class ImageRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_image_by_id(self, image_id: str) -> Image | None:
        db_image = self.db.query(ImageDB).filter(ImageDB.id == image_id).first()
        if db_image:
            return Image.model_validate(db_image)
        return None

    def create_image(self, image_data: Dict[str, Any]) -> Image: 
        db_image = ImageDB(**image_data)
        self.db.add(db_image)
        self.db.commit()
        self.db.refresh(db_image)
        return Image.model_validate(db_image)

    def list_images_by_user(self, user_id: int, page: int, limit: int) -> List[Image]:
        offset = (page - 1) * limit
        db_images = (
            self.db.query(ImageDB)
            .filter(ImageDB.user_id == user_id)
            # Use indexed user_id for filtering and order by ID for stable pagination
            .order_by(ImageDB.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [Image.model_validate(img) for img in db_images]

    def update_image(self, image_id: str, updates: Dict[str, Any]) -> Image | None:
        db_image = self.db.query(ImageDB).filter(ImageDB.id == image_id).first()
        if db_image:
            for key, value in updates.items():
                setattr(db_image, key, value)
            self.db.commit()
            self.db.refresh(db_image)
            return Image.model_validate(db_image)
        return None