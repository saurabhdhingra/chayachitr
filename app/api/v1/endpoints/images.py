from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from fastapi.responses import FileResponse, RedirectResponse 
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.core.exceptions import ImageNotFoundError
from app.core.dependencies import get_current_user
from app.domain.entities.image import Image, Transformation
from app.domain.entities.user import User
from app.application.services.image_service import ImageService
from app.infrastructure.persistence.image_repository import ImageRepository
from app.infrastructure.adapters.google_cloud_storage_adapter import GoogleCloudStorageService 
from app.infrastructure.adapters.message_queue import KafkaProducerAdapter
from app.infrastructure.adapters.redis_adapter import RedisAdapter # NEW Import

router = APIRouter()

def get_image_service(db: Session = Depends(get_db)):
    repo = ImageRepository(db)
    storage = GoogleCloudStorageService() 
    producer = KafkaProducerAdapter()
    redis_adapter = RedisAdapter() 
    return ImageService(repo, storage, producer, redis_adapter)


@router.post("/", response_model=Image, status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    image_service: ImageService = Depends(get_image_service)
):
    """Upload an image and return its details."""
    # Basic validation
    if file.content_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
        raise status.HTTP_400_BAD_REQUEST("Invalid image format.")
        
    uploaded_image = await image_service.upload_image(file, current_user.id)
    return uploaded_image

@router.post("/{image_id}/transform", response_model=Image)
async def apply_transformations(
    image_id: str,
    transformations: Transformation,
    current_user: User = Depends(get_current_user),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Applies transformations to an image and triggers asynchronous processing.
    Returns the placeholder image details.
    """
    transformed_image = image_service.request_transformation(
        image_id, 
        current_user.id, 
        transformations
    )
    return transformed_image

@router.get("/{image_id}")
def retrieve_image(
    image_id: str,
    current_user: User = Depends(get_current_user),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Retrieve an image. 
    Returns a 307 Redirect to a time-limited GCS Signed URL for direct download.
    """
    try:
        signed_url = image_service.get_image_url(image_id, current_user.id)
        return RedirectResponse(url=signed_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    except ImageNotFoundError:
        raise ImageNotFoundError()
    except Exception as e:
        print(f"Error retrieving signed URL: {e}")
        raise status.HTTP_500_INTERNAL_SERVER_ERROR(detail="Could not generate external image URL due to internal error.")


@router.get("/", response_model=List[Image])
def list_images(
    page: int = Query(1, ge=1), 
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    image_service: ImageService = Depends(get_image_service)
):
    """Get a paginated list of images uploaded by the user."""
    return image_service.list_user_images(current_user.id, page, limit)