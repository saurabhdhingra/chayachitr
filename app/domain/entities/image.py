from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid

class Transformation(BaseModel):
    # This models the transformations requested in the API
    resize: Optional[Dict[str, int]] = None  
    crop: Optional[Dict[str, int]] = None    
    rotate: Optional[int] = None             
    watermark: Optional[str] = None          
    flip: Optional[bool] = None
    mirror: Optional[bool] = None
    compress_quality: Optional[int] = Field(None, ge=1, le=100)
    format: Optional[str] = None             
    filters: Optional[Dict[str, bool]] = None 
    
    # Generate a unique ID for the resulting image file based on transformations
    def get_hash_id(self, original_id: str) -> str:
        transform_str = str(self.model_dump(exclude_none=True))
        return f"{original_id}_{uuid.uuid5(uuid.NAMESPACE_DNS, transform_str).hex}"


class Image(BaseModel):
    id: str  
    user_id: int
    filename: str
    storage_url: str
    mimetype: str
    size_bytes: int
    image_metadata: Dict[str, Any] = Field(default_factory=dict) # RENAMED from 'metadata'
    is_transformed: bool = False
    
    class Config:
        from_attributes = True