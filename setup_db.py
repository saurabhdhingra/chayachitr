import os
import shutil
from app.core.database import engine
from app.infrastructure.database.models import BaseModel

STORAGE_DIR = "images_store"
if os.path.exists(STORAGE_DIR):
    shutil.rmtree(STORAGE_DIR)
os.makedirs(STORAGE_DIR)

print("Create database tables and cleaning storage directory...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Database setup complete. Storage directory created at './images_store'.")