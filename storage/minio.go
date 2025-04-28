package storage

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"

	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

// StorageClient represents a client for object storage
type StorageClient struct {
	Client     *minio.Client
	BucketName string
}

// NewMinioClient creates a new MinIO client
func NewMinioClient() (*StorageClient, error) {
	// Get MinIO configuration from environment variables
	endpoint := os.Getenv("MINIO_ENDPOINT")
	if endpoint == "" {
		endpoint = "localhost:9000"
	}

	accessKey := os.Getenv("MINIO_ACCESS_KEY")
	if accessKey == "" {
		accessKey = "minioadmin"
	}

	secretKey := os.Getenv("MINIO_SECRET_KEY")
	if secretKey == "" {
		secretKey = "minioadmin"
	}

	useSSLStr := os.Getenv("MINIO_USE_SSL")
	useSSL := false
	if useSSLStr != "" {
		var err error
		useSSL, err = strconv.ParseBool(useSSLStr)
		if err != nil {
			useSSL = false
		}
	}

	bucketName := os.Getenv("MINIO_BUCKET_NAME")
	if bucketName == "" {
		bucketName = "chayachitr-images"
	}

	// Create MinIO client
	client, err := minio.New(endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(accessKey, secretKey, ""),
		Secure: useSSL,
	})
	if err != nil {
		return nil, err
	}

	// Check if bucket exists
	exists, err := client.BucketExists(context.Background(), bucketName)
	if err != nil {
		return nil, err
	}

	// Create bucket if it doesn't exist
	if !exists {
		err = client.MakeBucket(context.Background(), bucketName, minio.MakeBucketOptions{})
		if err != nil {
			return nil, err
		}
	}

	return &StorageClient{
		Client:     client,
		BucketName: bucketName,
	}, nil
}

// UploadImage uploads an image to the storage
func (s *StorageClient) UploadImage(reader io.Reader, filename string, contentType string) (string, error) {
	// Upload the file
	objectName := filepath.Join("uploads", filename)
	_, err := s.Client.PutObject(context.Background(), s.BucketName, objectName, reader, -1, minio.PutObjectOptions{
		ContentType: contentType,
	})
	if err != nil {
		return "", err
	}

	return objectName, nil
}

// GetImageURL returns the URL for the image
func (s *StorageClient) GetImageURL(objectName string) (string, error) {
	// Get presigned URL for the image
	presignedURL, err := s.Client.PresignedGetObject(context.Background(), s.BucketName, objectName, 24*60*60, nil)
	if err != nil {
		return "", err
	}

	return presignedURL.String(), nil
}

// GetImage retrieves an image from storage
func (s *StorageClient) GetImage(objectName string) (io.ReadCloser, error) {
	// Get the object
	object, err := s.Client.GetObject(context.Background(), s.BucketName, objectName, minio.GetObjectOptions{})
	if err != nil {
		return nil, err
	}

	return object, nil
}

// DeleteImage deletes an image from storage
func (s *StorageClient) DeleteImage(objectName string) error {
	err := s.Client.RemoveObject(context.Background(), s.BucketName, objectName, minio.RemoveObjectOptions{})
	if err != nil {
		return err
	}
	return nil
}

// StoreTransformedImage stores a transformed image
func (s *StorageClient) StoreTransformedImage(reader io.Reader, originalObjectName, transformationHash string, contentType string) (string, error) {
	ext := filepath.Ext(originalObjectName)
	transformedObjectName := fmt.Sprintf("%s_%s%s", originalObjectName[:len(originalObjectName)-len(ext)], transformationHash, ext)

	_, err := s.Client.PutObject(context.Background(), s.BucketName, transformedObjectName, reader, -1, minio.PutObjectOptions{
		ContentType: contentType,
	})
	if err != nil {
		return "", err
	}

	return transformedObjectName, nil
} 