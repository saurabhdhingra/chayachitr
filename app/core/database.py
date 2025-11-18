import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The database URL should typically be loaded from an environment variable (e.g., in a settings file)
# Replace this placeholder with your actual connection string if it's currently hardcoded here.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_EtcB04XFkimL@ep-rough-shadow-a15nwloo-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

# The engine is responsible for communicating with the database
engine = create_engine(DATABASE_URL)

# Base is the base class for all declarative models (like UserDB and ImageDB)
Base = declarative_base()

# SessionLocal is the class used to create database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()