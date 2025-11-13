from pydantic import BaseModel, Field
from typing import Optional, Dict

class Image(BaseModel):
    id: Optional[str] = None
    user_id: int
    filename: str
    storage_url: str
    mimetype: str
    size_bytes: int
    metadata: Dict[str, any] = Field(default_factory = dict)
    is_transformed: bool = False

    class Config:
        from_attributes = True

class Transformation(BaseModel):
# This models the transformations requested in the API
    resize: Optional[Dict[str, int]] = None  # {"width": 800, "height": 600}
    crop: Optional[Dict[str, int]] = None    # {"width": 200, "height": 200, "x": 10, "y": 10}
    rotate: Optional[int] = None             # 90
    watermark: Optional[str] = None          # "text" or "image_id"
    flip: Optional[bool] = None
    mirror: Optional[bool] = None
    compress_quality: Optional[int] = None   # 1-100
    format: Optional[str] = None             # "jpeg", "png", "webp"
    filters: Optional[Dict[str, bool]] = None # {"grayscale": True}