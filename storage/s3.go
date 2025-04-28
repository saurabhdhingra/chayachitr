package storage

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"io/ioutil"
	"os"
	"path/filepath"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
)

// S3StorageClient represents a client for AWS S3 storage
type S3StorageClient struct {
	Session    *session.Session
	S3Client   *s3.S3
	Uploader   *s3manager.Uploader
	Downloader *s3manager.Downloader
	BucketName string
	Region     string
}

// NewS3Client creates a new AWS S3 client
func NewS3Client() (*S3StorageClient, error) {
	// Get S3 configuration from environment variables
	accessKey := os.Getenv("S3_ACCESS_KEY")
	secretKey := os.Getenv("S3_SECRET_KEY")
	region := os.Getenv("S3_REGION")
	if region == "" {
		region = "us-east-1"
	}

	bucketName := os.Getenv("S3_BUCKET_NAME")
	if bucketName == "" {
		return nil, fmt.Errorf("S3_BUCKET_NAME environment variable is required")
	}

	// Create AWS session
	sess, err := session.NewSession(&aws.Config{
		Region:      aws.String(region),
		Credentials: credentials.NewStaticCredentials(accessKey, secretKey, ""),
	})
	if err != nil {
		return nil, err
	}

	// Create S3 service client
	s3Client := s3.New(sess)

	// Check if bucket exists
	_, err = s3Client.HeadBucket(&s3.HeadBucketInput{
		Bucket: aws.String(bucketName),
	})
	if err != nil {
		// If bucket doesn't exist, create it
		_, err = s3Client.CreateBucket(&s3.CreateBucketInput{
			Bucket: aws.String(bucketName),
		})
		if err != nil {
			return nil, err
		}

		// Wait for bucket to be created
		err = s3Client.WaitUntilBucketExists(&s3.HeadBucketInput{
			Bucket: aws.String(bucketName),
		})
		if err != nil {
			return nil, err
		}
	}

	return &S3StorageClient{
		Session:    sess,
		S3Client:   s3Client,
		Uploader:   s3manager.NewUploader(sess),
		Downloader: s3manager.NewDownloader(sess),
		BucketName: bucketName,
		Region:     region,
	}, nil
}

// UploadImage uploads an image to S3
func (s *S3StorageClient) UploadImage(reader io.Reader, filename string, contentType string) (string, error) {
	// Read the entire file into memory
	fileBytes, err := ioutil.ReadAll(reader)
	if err != nil {
		return "", err
	}

	// Upload the file
	objectName := filepath.Join("uploads", filename)
	_, err = s.Uploader.Upload(&s3manager.UploadInput{
		Bucket:      aws.String(s.BucketName),
		Key:         aws.String(objectName),
		Body:        bytes.NewReader(fileBytes),
		ContentType: aws.String(contentType),
	})
	if err != nil {
		return "", err
	}

	return objectName, nil
}

// GetImageURL returns the URL for the image
func (s *S3StorageClient) GetImageURL(objectName string) (string, error) {
	// Generate a presigned URL for the image
	req, _ := s.S3Client.GetObjectRequest(&s3.GetObjectInput{
		Bucket: aws.String(s.BucketName),
		Key:    aws.String(objectName),
	})
	
	urlStr, err := req.Presign(24 * time.Hour) // URL valid for 24 hours
	if err != nil {
		return "", err
	}

	return urlStr, nil
}

// GetImage retrieves an image from S3
func (s *S3StorageClient) GetImage(objectName string) (io.ReadCloser, error) {
	// Create a buffer to write the file content
	writer := aws.NewWriteAtBuffer([]byte{})

	// Download the file
	_, err := s.Downloader.Download(writer, &s3.GetObjectInput{
		Bucket: aws.String(s.BucketName),
		Key:    aws.String(objectName),
	})
	if err != nil {
		return nil, err
	}

	// Create a ReadCloser from the buffer
	return io.NopCloser(bytes.NewReader(writer.Bytes())), nil
}

// DeleteImage deletes an image from S3
func (s *S3StorageClient) DeleteImage(objectName string) error {
	_, err := s.S3Client.DeleteObject(&s3.DeleteObjectInput{
		Bucket: aws.String(s.BucketName),
		Key:    aws.String(objectName),
	})
	if err != nil {
		return err
	}

	// Wait for the object to be deleted
	err = s.S3Client.WaitUntilObjectNotExists(&s3.HeadObjectInput{
		Bucket: aws.String(s.BucketName),
		Key:    aws.String(objectName),
	})
	if err != nil {
		return err
	}

	return nil
}

// StoreTransformedImage stores a transformed image
func (s *S3StorageClient) StoreTransformedImage(reader io.Reader, originalObjectName, transformationHash string, contentType string) (string, error) {
	// Read the entire file into memory
	fileBytes, err := ioutil.ReadAll(reader)
	if err != nil {
		return "", err
	}

	// Generate a new object name
	ext := filepath.Ext(originalObjectName)
	transformedObjectName := fmt.Sprintf("%s_%s%s", originalObjectName[:len(originalObjectName)-len(ext)], transformationHash, ext)

	// Upload the transformed image
	_, err = s.Uploader.Upload(&s3manager.UploadInput{
		Bucket:      aws.String(s.BucketName),
		Key:         aws.String(transformedObjectName),
		Body:        bytes.NewReader(fileBytes),
		ContentType: aws.String(contentType),
	})
	if err != nil {
		return "", err
	}

	return transformedObjectName, nil
} 