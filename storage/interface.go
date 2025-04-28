package storage

import "io"

// StorageInterface defines the common interface for storage providers
type StorageInterface interface {
	// UploadImage uploads an image and returns its object name
	UploadImage(reader io.Reader, filename string, contentType string) (string, error)
	
	// GetImageURL returns the URL for accessing an image
	GetImageURL(objectName string) (string, error)
	
	// GetImage retrieves an image by its object name
	GetImage(objectName string) (io.ReadCloser, error)
	
	// DeleteImage deletes an image by its object name
	DeleteImage(objectName string) error
	
	// StoreTransformedImage stores a transformed version of an image
	StoreTransformedImage(reader io.Reader, originalObjectName, transformationHash string, contentType string) (string, error)
} 