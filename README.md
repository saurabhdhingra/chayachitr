# Chayachitr - Image Processing Service

Chayachitr is a REST API service for image processing, similar to Cloudinary. It allows users to upload images, apply various transformations, and retrieve images in different formats.

## Features

- **User Authentication**: Sign-up, login, and JWT-based authentication
- **Image Management**: Upload, retrieve, and list images
- **Image Transformation**: Resize, crop, rotate, watermark, filter, format conversion, and more

## Prerequisites

- Go 1.21 or higher
- MongoDB
- MinIO (for object storage)

## Setup

1. Clone the repository:

   ```
   git clone https://github.com/yourname/chayachitr.git
   cd chayachitr
   ```

2. Install dependencies:

   ```
   go mod download
   ```

3. Set up environment variables:

   - Copy `.env.example` to `.env`
   - Modify the values as needed

4. Set up MinIO:

   - Install MinIO or use a cloud storage service
   - Update the MinIO credentials in `.env`

5. Run the application:
   ```
   go run main.go
   ```

## API Endpoints

### Authentication

- **Register a user**:

  ```
  POST /register
  {
    "username": "user1",
    "password": "password123"
  }
  ```

- **Login**:
  ```
  POST /login
  {
    "username": "user1",
    "password": "password123"
  }
  ```

### Image Management

- **Upload an image**:

  ```
  POST /images
  Form-data: file=@image.jpg
  ```

- **Apply transformations**:

  ```
  POST /images/:id/transform
  {
    "transformations": {
      "resize": { "width": 800, "height": 600 },
      "crop": { "width": 400, "height": 300, "x": 0, "y": 0 },
      "rotate": 90,
      "format": "png",
      "filters": { "grayscale": true }
    }
  }
  ```

- **Retrieve an image**:

  ```
  GET /images/:id
  ```

- **List images**:
  ```
  GET /images?page=1&limit=10
  ```

## Technologies Used

- [Go](https://golang.org/): Programming language
- [Gin](https://github.com/gin-gonic/gin): Web framework
- [JWT](https://github.com/dgrijalva/jwt-go): Authentication
- [MongoDB](https://www.mongodb.com/): Database
- [MinIO](https://min.io/): Object storage
- [Imaging](https://github.com/disintegration/imaging): Image processing

## License

This project is licensed under the MIT License - see the LICENSE file for details.
