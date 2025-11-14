from typing import List, Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.core.exceptions import ImageNotFoundError
from app.core.config import settings
from app.domain.entities.image import Image, Transformation
from app.infrastructure.persistence.image_repository import ImageRepository
from app.infrastructure.adapters.google_cloud_storage_adapter import GoogleCloudStorageService 
from app.infrastructure.adapters.message_queue import KafkaProducerAdapter
from app.infrastructure.adapters.redis_adapter import RedisAdapter # NEW Import


StorageService = GoogleCloudStorageService 

class ImageService:
    def __init__(self, repo: ImageRepository, storage: StorageService, producer: KafkaProducerAdapter, redis: RedisAdapter): 
        self.repo = repo
        self.storage = storage
        self.producer = producer
        self.redis = redis # NEW

    async def upload_image(self, file: UploadFile, user_id: int) -> Image:
        """Uploads image to storage and saves metadata to DB."""
        image_id, storage_url, size_bytes = await self.storage.upload_image(file, user_id)
        
        image_data = {
            "id": image_id,
            "user_id": user_id,
            "filename": file.filename,
            "storage_url": storage_url, 
            "mimetype": file.content_type,
            "size_bytes": size_bytes,
            "metadata": {"original_filename": file.filename}
        }
        return self.repo.create_image(image_data)

    def request_transformation(self, original_id: str, user_id: int, transformations: Transformation) -> Image:
        """
        Validates image ownership, generates a transformation request, 
        and sends it to the message queue.
        """
        original_image = self.repo.get_image_by_id(original_id)
        
        if not original_image or original_image.user_id != user_id:
            raise ImageNotFoundError()
            
        # 1. Generate new image ID based on transformations
        new_id = transformations.get_hash_id(original_id)
        
        # 2. Check cache/DB for pre-existing transformed image
        cached_image = self.repo.get_image_by_id(new_id)
        if cached_image and cached_image.is_transformed:
            # Found in cache/DB, return immediately
            return cached_image
            
        # 3. Create a placeholder entry for the new image in DB (for status tracking)
        if not cached_image:
             placeholder_data = {
                "id": new_id,
                "user_id": user_id,
                "filename": f"transformed_{original_image.filename}",
                "storage_url": original_image.storage_url, # Original path until processed
                "mimetype": original_image.mimetype,
                "size_bytes": 0,
                "metadata": transformations.model_dump(exclude_none=True),
                "is_transformed": False
            }
             placeholder_image = self.repo.create_image(placeholder_data)
        else:
             placeholder_image = cached_image
        
        # 4. Send asynchronous request to Kafka
        self.producer.send_transformation_request(original_id, new_id, transformations, user_id)
        
        return placeholder_image

    def get_image_url(self, image_id: str, user_id: int) -> str:
        """
        Retrieves a time-limited signed URL for direct client access to the GCS object.
        Implements caching for the signed URL.
        """
        image = self.repo.get_image_by_id(image_id)
        if not image or image.user_id != user_id:
            raise ImageNotFoundError()
            
        cache_key = f"image_url:{image_id}"
        
        # 1. Check Redis Cache
        cached_url = self.redis.get(cache_key)
        if cached_url:
            print(f"Serving signed URL for {image_id} from Redis cache.")
            return cached_url
            
        # 2. Generate new Signed URL
        # The storage_url holds the GCS object path (blob name). 
        signed_url = self.storage.generate_signed_url(image.storage_url) 

        # 3. Store in Redis Cache
        # Use a TTL slightly shorter than the GCS expiration to avoid serving expired links
        ttl = settings.IMAGE_URL_CACHE_SECONDS 
        self.redis.set(cache_key, signed_url, ttl)
        print(f"Generated and cached signed URL for {image_id}.")
        
        return signed_url

    def list_user_images(self, user_id: int, page: int, limit: int) -> List[Image]:
        """Lists images for a specific user."""
        return self.repo.list_images_by_user(user_id, page, limit)