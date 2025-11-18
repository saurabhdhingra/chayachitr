import os
import shutil
from app.core.database import engine, Base
from app.infrastructure.database import models 

# Set up storage directory
STORAGE_DIR = "images_store"
if os.path.exists(STORAGE_DIR):
    shutil.rmtree(STORAGE_DIR)
os.makedirs(STORAGE_DIR)

# Drop and recreate all tables
print("Creating database tables and cleaning storage directory...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Database setup complete. Storage directory created at './images_store'.")
