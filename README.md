# Image Processor Microservice

## Project Description

This project is a high-performance, event-driven image processing microservice built with FastAPI in Python. It provides secure APIs for users to upload, manage, and request asynchronous transformations (like resizing, watermarking, or filtering) on their images.

The architecture is designed for scalability and durability, leveraging Google Cloud Storage (GCS) for file storage, Kafka for asynchronous processing, PostgreSQL (or SQLite) for metadata persistence, and Redis for rate limiting and signed URL caching.

## Architecture Flowchart

The system follows an event-driven pattern for transformations and a cache-first approach for serving content.

<img width="1024" height="1024" alt="Gemini_Generated_Image_n39uqgn39uqgn39u" src="https://github.com/user-attachments/assets/0c558cdf-5ea1-4ae1-b3cb-6b795c1a99b6" />

## Architectural Components

```
Component           Technology                  Role

API Gateway         FastAPI (Python)            Handles all synchronous requests, authentication, rate 
                                                limiting, and business logic orchestration.

Database            SQLAlchemy (PostgreSQL      Persistent storage for user and image metadata 
                    /SQLite)                    (filenames, storage paths, transformation status).

Storage             Google Cloud Storage (GCS)  Durable, scalable storage for raw and transformed image 
                                                files. Secure access via time-limited Signed URLs.

Message Queue       Kafka                       Decouples the request (API) from the processing (Worker), 
                                                ensuring fast response times and reliable, asynchronous job 
                                                execution.

Caching/State       Redis                       Used for high-speed caching of GCS Signed URLs and 
                                                implementing application-wide rate limiting.

Worker Service      Separate Process (Consumer) Consumes messages from Kafka, downloads images, applies 
                                                transformations (e.g., using Pillow), and updates GCS and the database.
```

Folder Structure

The project follows a clean Domain-Driven Design (DDD) inspired structure:

```
.
├── app/
│   ├── api/                     # Interface Layer (FastAPI Endpoints)
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── auth.py      # /api/v1/login, /api/v1/register
│   │           └── images.py    # /api/v1/images/...
│   │
│   ├── application/             # Application Layer (Business Logic Orchestrators)
│   │   └── services/
│   │       ├── auth_service.py
│   │       └── image_service.py
│   │
│   ├── core/                    # Cross-cutting concerns (Global setup, dependencies)
│   │   ├── config.py            # UPDATED: Includes REDIS_HOST, REDIS_PORT
│   │   ├── database.py
│   │   ├── dependencies.py      # Authentication dependency
│   │   ├── exceptions.py
│   │   └── middlewares.py       # UPDATED: Rate limiting using Redis
│   │
│   ├── domain/                  # Domain Layer (The heart of the app: entities and rules)
│   │   └── entities/
│   │       ├── image.py
│   │       └── user.py
│   │
│   ├── infrastructure/          # Infrastructure Layer (External components: DB, Storage, MQ)
│   │   ├── adapters/            # Implementations of external services
│   │   │   ├── image_processor.py  # PIL adapter
│   │   │   ├── message_queue.py    # Kafka adapter
│   │   │   └── storage_service.py  # Local file storage mock
│   │   ├── database/
│   │   │   └── models.py        # SQLAlchemy models (DB schemas)
│   │   └── persistence/         # Repository implementations
│   │       ├── image_repository.py
│   │       └── user_repository.py
│   │
│   └── main.py                  # FastAPI Application Entry Point
│
├── images_store/                # Local file system storage (mimics GCS bucket)
├── .env                         # Environment variables (REDIS_HOST, SECRET_KEY, etc.)
├── requirements.txt             # Dependency list (now includes 'redis')
└── setup_db.py                  # Setup script for creating SQLite tables and storage directory
```

## Project Setup Guide

### 1. Prerequisites

- Python 3.10+

- Docker (for running Kafka and Redis)

- A Google Cloud Project and GCS Bucket

- GCP Service Account credentials

### 2. Environment Setup

Create a `.env` file in the project root:

```
# Database
DATABASE_URL=sqlite:///./sql_app.db # Use postgresql://... in production

# JWT
SECRET_KEY="A_STRONG_SECRET_KEY"

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Google Cloud Storage
GCS_BUCKET_NAME=my-image-processor-bucket-001
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

### 4. Run External Services (Kafka & Redis)

Use Docker Compose or run locally:

```
# Example command to start local Kafka/Redis infrastructure (if using Docker)
# docker-compose up -d kafka redis
```

### 5. GCP Authentication

You must authenticate your environment for the GCS adapter to work:

```
# Authenticate your local environment using Application Default Credentials
gcloud auth application-default login
```

Ensure the bucket specified by GCS_BUCKET_NAME exists and the credentials have write access.

### 6. Run Migrations

Initialize the database tables:

```
# This usually runs inside your application startup or a dedicated script
python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine); print('DB initialized.')"
```

### 7. Run Services

**A. Run FastAPI Server:**

```
uvicorn app.main:app --reload
```

**B. Run Worker Service (in a separate terminal):**

```
python worker/consumer.py
```

## API Endpoint Usage Examples

All examples assume the API is running at `http://localhost:8000/api/v1` and you have a valid JWT access token (omitted for brevity).

**1. Upload an Image (**`POST /images/`**)**

Uploads a file and stores it in GCS, returning the metadata.

```
curl -X POST "http://localhost:8000/api/v1/images/" \
     -H "Authorization: Bearer <JWT_TOKEN>" \
     -F "file=@./path/to/my_photo.jpg" 
```

**Example Response (201 CREATED):**

```
{
  "id": "e4f8d689-...",
  "user_id": 1,
  "filename": "my_photo.jpg",
  "storage_url": "1/e4f8d689-....jpg",
  "is_transformed": false,
  "mimetype": "image/jpeg",
  "size_bytes": 102400,
  "created_at": "2025-01-01T10:00:00"
}
```

**2. Request a Transformation (**`POST /images/{image_id}/transform`**)**

Requests an asynchronous transformation. Returns a placeholder image entry immediately.

```
IMAGE_ID="e4f8d689-..."

curl -X POST "http://localhost:8000/api/v1/images/${IMAGE_ID}/transform" \
     -H "Authorization: Bearer <JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{
           "resize": {"width": 800, "height": 600},
           "grayscale": true,
           "format": "png"
         }'
```

**Example Response (200 OK):**
*Note: The ID will be a hash of the original ID and transformation parameters.*

```
{
  "id": "f5a7b3c2-...", 
  "user_id": 1,
  "filename": "transformed_my_photo.jpg",
  "is_transformed": false, # Will be set to true by the worker later
  "metadata": {"resize": {"width": 800, "height": 600}, "grayscale": true, "format": "png"},
  "status": "PROCESSING",
  "created_at": "2025-01-01T10:01:00"
}
```

**3. Retrieve an Image (**`GET /images/{image_id}`**)**

Retrieves the image file. This endpoint performs a 307 Redirect to a cached GCS Signed URL.

```
# This command will automatically follow the redirect to the GCS Signed URL
IMAGE_ID="e4f8d689-..."

curl -L -X GET "http://localhost:8000/api/v1/images/${IMAGE_ID}" \
     -H "Authorization: Bearer <JWT_TOKEN>"
```

**Response (307 TEMPORARY REDIRECT):**
The API returns a 307 status code with a `Location` header pointing to the temporary GCS URL (e.g., `https://storage.googleapis.com/...signed_url_parameters`). The client (browser/curl) must follow this redirect.

```
HTTP/1.1 307 Temporary Redirect
Location: [https://storage.googleapis.com/my-image-processor-bucket-001/1/f5a7b3c2-....png?X-Goog-Signature=](https://storage.googleapis.com/my-image-processor-bucket-001/1/f5a7b3c2-....png?X-Goog-Signature=)...
```

## Acknowledgement
https://roadmap.sh/projects/image-processing-service
