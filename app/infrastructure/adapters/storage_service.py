import os
import uuid
from fastapi import UploadFile
from app.core.config import settings
from typing import Tuple
from google.cloud import storage 
from datetime import timedelta

class GoogleCloudStorageService:
    """
    Implements actual Google Cloud Storage interactions.
    storage_url now represents the GCS object path (e.g., '1/uuid.jpg').
    """
    def __init__(self):
        self.bucket_name = settings.GCS_BUCKET_NAME
        
        try:
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            print(f"GCS Client connected to bucket: {self.bucket_name}")
        except Exception as e:
            print(f"WARNING: GCS client initialization failed. Please check credentials and bucket name. Error: {e}")
            self.client = None
            self.bucket = None
            
        self.storage_root = settings.STORAGE_PATH 

    def _get_gcs_path(self, user_id: int, file_id: str, filename: str) -> str:
        """Helper to generate the object path (blob name) in GCS format."""
        file_extension = os.path.splitext(filename)[1]
        # GCS path structure: {user_id}/{file_id}{extension}
        return f"{user_id}/{file_id}{file_extension}"

    async def upload_image(self, file: UploadFile, user_id: int) -> Tuple[str, str, int]:
        """
        Uploads an image directly to GCS from an UploadFile object. 
        Returns (image_id, storage_url/gcs_path, size_bytes).
        """
        if not self.bucket:
             raise Exception("GCS not initialized. Cannot upload.")
             
        image_id = str(uuid.uuid4())
        
        gcs_path = self._get_gcs_path(user_id, image_id, file.filename)
        
        blob = self.bucket.blob(gcs_path)
        
        file_data = await file.read()
        size_bytes = len(file_data)
        
        await file.seek(0)
        
        blob.upload_from_string(
            file_data, 
            content_type=file.content_type
        )
        
        storage_url = gcs_path
        
        return image_id, storage_url, size_bytes

    def save_transformed_image(self, image_data: bytes, user_id: int, original_filename: str, new_id: str) -> str:
        """
        Saves a transformed image from raw bytes to GCS. Used primarily by the worker.
        Returns the GCS path (storage_url) for the new image.
        """
        if not self.bucket:
             raise Exception("GCS not initialized. Cannot save transformed image.")
             
        gcs_path = self._get_gcs_path(user_id, new_id, original_filename)
        
        blob = self.bucket.blob(gcs_path)
        
        blob.upload_from_string(image_data) 
            
        return gcs_path 

    def download_image(self, storage_url: str) -> bytes:
        """
        Downloads the image data from GCS for processing (Worker use).
        """
        if not self.bucket:
             raise Exception("GCS not initialized. Cannot download image.")
             
        blob = self.bucket.blob(storage_url)
        
        if not blob.exists():
            raise FileNotFoundError(f"Image object not found at GCS path: {storage_url}")
        

        return blob.download_as_bytes()
        
    def generate_signed_url(self, storage_url: str) -> str:
        """
        Generates a time-limited signed URL for direct client access to the GCS object.
        """
        if not self.bucket:
             return f"/api/v1/images/unavailable/{storage_url}"
             
        blob = self.bucket.blob(storage_url)
        
        expiration_time = timedelta(seconds=settings.GCS_SIGNED_URL_EXPIRATION_SECONDS)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_time,
            method="GET"
        )
        return url