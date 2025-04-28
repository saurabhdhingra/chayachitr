package controllers

import (
	"bytes"
	"context"
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"path/filepath"
	"strconv"
	"time"

	"github.com/disintegration/imaging"
	"github.com/gin-gonic/gin"
	"github.com/go-playground/validator/v10"
	"github.com/yourname/chayachitr/config"
	"github.com/yourname/chayachitr/models"
	"github.com/yourname/chayachitr/storage"
	"github.com/yourname/chayachitr/utils"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// ImageController handles image-related requests
type ImageController struct {
	DB           *config.Database
	StorageClient *storage.StorageClient
	Validator    *validator.Validate
}

// NewImageController creates a new ImageController
func NewImageController(db *config.Database, storageClient *storage.StorageClient) *ImageController {
	return &ImageController{
		DB:           db,
		StorageClient: storageClient,
		Validator:    validator.New(),
	}
}

// UploadImage handles image upload
func (ic *ImageController) UploadImage(c *gin.Context) {
	// Get user ID from context
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User ID not found in context"})
		return
	}

	// Parse multipart form
	err := c.Request.ParseMultipartForm(utils.MaxFileSize)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to parse form"})
		return
	}

	// Get file from form
	file, header, err := c.Request.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "File is required"})
		return
	}
	defer file.Close()

	// Validate file
	valid, errMsg := utils.ValidateImageFile(header)
	if !valid {
		c.JSON(http.StatusBadRequest, gin.H{"error": errMsg})
		return
	}

	// Generate a unique ID for the file
	uniqueID, err := utils.GenerateUniqueID()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to generate unique ID"})
		return
	}

	// Append original extension to unique ID
	ext := filepath.Ext(header.Filename)
	filename := uniqueID + ext

	contentType := header.Header.Get("Content-Type")

	// Upload file to storage
	objectName, err := ic.StorageClient.UploadImage(file, filename, contentType)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to upload image"})
		return
	}

	// Get image URL
	url, err := ic.StorageClient.GetImageURL(objectName)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get image URL"})
		return
	}

	// Create image record
	image := models.Image{
		UserID:       userID.(primitive.ObjectID),
		Filename:     filename,
		ContentType:  contentType,
		Size:         header.Size,
		ObjectName:   objectName,
		URL:          url,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	// Insert image into database
	collection := ic.DB.GetCollection("images")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	result, err := collection.InsertOne(ctx, image)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Get the inserted ID
	image.ID = result.InsertedID.(primitive.ObjectID)

	c.JSON(http.StatusCreated, image)
}

// GetImage handles retrieving an image
func (ic *ImageController) GetImage(c *gin.Context) {
	// Get user ID from context
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User ID not found in context"})
		return
	}

	// Get image ID from URL parameter
	imageID, err := primitive.ObjectIDFromHex(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid image ID"})
		return
	}

	// Find image in database
	collection := ic.DB.GetCollection("images")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	var image models.Image
	err = collection.FindOne(ctx, bson.M{
		"_id":     imageID,
		"user_id": userID,
	}).Decode(&image)

	if err != nil {
		if err == mongo.ErrNoDocuments {
			c.JSON(http.StatusNotFound, gin.H{"error": "Image not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}
		return
	}

	// Update image URL (in case it has expired)
	url, err := ic.StorageClient.GetImageURL(image.ObjectName)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get image URL"})
		return
	}
	image.URL = url

	c.JSON(http.StatusOK, image)
}

// ListImages handles listing images
func (ic *ImageController) ListImages(c *gin.Context) {
	// Get user ID from context
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User ID not found in context"})
		return
	}

	// Get page and limit from query parameters
	page, err := strconv.ParseInt(c.DefaultQuery("page", "1"), 10, 64)
	if err != nil || page < 1 {
		page = 1
	}

	limit, err := strconv.ParseInt(c.DefaultQuery("limit", "10"), 10, 64)
	if err != nil || limit < 1 || limit > 100 {
		limit = 10
	}

	// Calculate skip value
	skip := (page - 1) * limit

	// Find images in database
	collection := ic.DB.GetCollection("images")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Set up find options
	findOptions := options.Find()
	findOptions.SetSkip(skip)
	findOptions.SetLimit(limit)
	findOptions.SetSort(bson.M{"created_at": -1})

	// Find images for the user
	cursor, err := collection.Find(ctx, bson.M{"user_id": userID}, findOptions)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer cursor.Close(ctx)

	// Decode images
	var images []models.Image
	if err := cursor.All(ctx, &images); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Update image URLs (in case they have expired)
	for i := range images {
		url, err := ic.StorageClient.GetImageURL(images[i].ObjectName)
		if err != nil {
			continue
		}
		images[i].URL = url
	}

	// Count total images
	totalCount, err := collection.CountDocuments(ctx, bson.M{"user_id": userID})
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Calculate total pages
	totalPages := int64(math.Ceil(float64(totalCount) / float64(limit)))

	// Create response
	response := models.ImageListResponse{
		Images:      images,
		TotalCount:  totalCount,
		PageSize:    limit,
		CurrentPage: page,
		TotalPages:  totalPages,
	}

	c.JSON(http.StatusOK, response)
}

// TransformImage handles transforming an image
func (ic *ImageController) TransformImage(c *gin.Context) {
	// Get user ID from context
	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "User ID not found in context"})
		return
	}

	// Get image ID from URL parameter
	imageID, err := primitive.ObjectIDFromHex(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid image ID"})
		return
	}

	// Parse transformation parameters from request body
	var requestBody struct {
		Transformations models.TransformParams `json:"transformations" validate:"required"`
	}

	if err := c.ShouldBindJSON(&requestBody); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate transformation parameters
	if err := ic.Validator.Struct(requestBody); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Find image in database
	collection := ic.DB.GetCollection("images")
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	var image models.Image
	err = collection.FindOne(ctx, bson.M{
		"_id":     imageID,
		"user_id": userID,
	}).Decode(&image)

	if err != nil {
		if err == mongo.ErrNoDocuments {
			c.JSON(http.StatusNotFound, gin.H{"error": "Image not found"})
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		}
		return
	}

	// Calculate a hash of the transformation parameters to use as a cache key
	paramsJSON, err := json.Marshal(requestBody.Transformations)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to process transformation parameters"})
		return
	}
	hash := md5.Sum(paramsJSON)
	transformationHash := hex.EncodeToString(hash[:])

	// Check if transformation already exists
	transformationCollection := ic.DB.GetCollection("transformations")
	var existingTransformation models.Transformation
	err = transformationCollection.FindOne(ctx, bson.M{
		"image_id": imageID,
		"hash":     transformationHash,
	}).Decode(&existingTransformation)

	if err == nil {
		// Transformation already exists, update URL and return
		url, err := ic.StorageClient.GetImageURL(existingTransformation.ObjectName)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get transformation URL"})
			return
		}
		existingTransformation.URL = url
		c.JSON(http.StatusOK, existingTransformation)
		return
	} else if err != mongo.ErrNoDocuments {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Get the original image from storage
	imageReader, err := ic.StorageClient.GetImage(image.ObjectName)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get original image"})
		return
	}
	defer imageReader.Close()

	// Decode the image
	srcImage, err := imaging.Decode(imageReader)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to decode image"})
		return
	}

	// Apply transformations
	dstImage := srcImage

	// Resize
	if requestBody.Transformations.Resize != nil {
		dstImage = imaging.Resize(dstImage, requestBody.Transformations.Resize.Width, requestBody.Transformations.Resize.Height, imaging.Lanczos)
	}

	// Crop
	if requestBody.Transformations.Crop != nil {
		dstImage = imaging.Crop(dstImage, imaging.Rectangle{
			Min: imaging.Point{X: requestBody.Transformations.Crop.X, Y: requestBody.Transformations.Crop.Y},
			Max: imaging.Point{X: requestBody.Transformations.Crop.X + requestBody.Transformations.Crop.Width, Y: requestBody.Transformations.Crop.Y + requestBody.Transformations.Crop.Height},
		})
	}

	// Rotate
	if requestBody.Transformations.Rotate != nil {
		dstImage = imaging.Rotate(dstImage, *requestBody.Transformations.Rotate, imaging.Color{})
	}

	// Flip
	if requestBody.Transformations.Flip != nil && *requestBody.Transformations.Flip {
		dstImage = imaging.FlipV(dstImage)
	}

	// Mirror
	if requestBody.Transformations.Mirror != nil && *requestBody.Transformations.Mirror {
		dstImage = imaging.FlipH(dstImage)
	}

	// Apply filters
	if requestBody.Transformations.Filters != nil {
		// Grayscale
		if requestBody.Transformations.Filters.Grayscale {
			dstImage = imaging.Grayscale(dstImage)
		}

		// Sepia
		if requestBody.Transformations.Filters.Sepia {
			dstImage = imaging.Sepia(dstImage)
		}

		// Blur
		if requestBody.Transformations.Filters.Blur != nil {
			dstImage = imaging.Blur(dstImage, *requestBody.Transformations.Filters.Blur)
		}

		// Sharpen
		if requestBody.Transformations.Filters.Sharpen != nil {
			dstImage = imaging.Sharpen(dstImage, *requestBody.Transformations.Filters.Sharpen)
		}
	}

	// Apply watermark
	if requestBody.Transformations.Watermark != nil {
		dstImage = utils.AddWatermark(
			dstImage,
			requestBody.Transformations.Watermark.Text,
			requestBody.Transformations.Watermark.X,
			requestBody.Transformations.Watermark.Y,
			requestBody.Transformations.Watermark.Opacity,
		)
	}

	// Initialize buffer to hold the encoded image
	var buf bytes.Buffer

	// Determine output format
	format := imaging.JPEG
	contentType := "image/jpeg"
	if requestBody.Transformations.Format != nil {
		switch *requestBody.Transformations.Format {
		case "png":
			format = imaging.PNG
			contentType = "image/png"
		case "gif":
			format = imaging.GIF
			contentType = "image/gif"
		}
	} else {
		// Use original format if none specified
		switch filepath.Ext(image.Filename) {
		case ".png":
			format = imaging.PNG
			contentType = "image/png"
		case ".gif":
			format = imaging.GIF
			contentType = "image/gif"
		}
	}

	// Encode the transformed image
	err = imaging.Encode(&buf, dstImage, format)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to encode transformed image"})
		return
	}

	// Store the transformed image
	transformedObjectName, err := ic.StorageClient.StoreTransformedImage(
		bytes.NewReader(buf.Bytes()),
		image.ObjectName,
		transformationHash,
		contentType,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to store transformed image"})
		return
	}

	// Get URL for the transformed image
	transformedURL, err := ic.StorageClient.GetImageURL(transformedObjectName)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to get transformed image URL"})
		return
	}

	// Create transformation record
	transformation := models.Transformation{
		ID:         primitive.NewObjectID(),
		ImageID:    imageID,
		ObjectName: transformedObjectName,
		URL:        transformedURL,
		Parameters: requestBody.Transformations,
		Hash:       transformationHash,
		CreatedAt:  time.Now(),
	}

	// Insert transformation into database
	_, err = transformationCollection.InsertOne(ctx, transformation)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// Update the image's transformations array
	_, err = collection.UpdateOne(
		ctx,
		bson.M{"_id": imageID},
		bson.M{
			"$push": bson.M{"transformations": transformation},
			"$set":  bson.M{"updated_at": time.Now()},
		},
	)
	if err != nil {
		fmt.Println("Failed to update image with transformation:", err)
	}

	c.JSON(http.StatusCreated, transformation)
} 