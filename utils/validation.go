package utils

import (
	"crypto/rand"
	"encoding/hex"
	"mime/multipart"
	"path/filepath"
	"strings"
)

// MaxFileSize defines the maximum allowed file size (10MB)
const MaxFileSize = 10 << 20

// SupportedImageTypes defines the supported image MIME types
var SupportedImageTypes = map[string]bool{
	"image/jpeg": true,
	"image/png":  true,
	"image/gif":  true,
}

// ValidateImageFile validates an uploaded image file
func ValidateImageFile(file *multipart.FileHeader) (bool, string) {
	// Check file size
	if file.Size > MaxFileSize {
		return false, "File size exceeds limit (10MB)"
	}

	// Check file type
	contentType := file.Header.Get("Content-Type")
	if !SupportedImageTypes[contentType] {
		return false, "File type not supported (only JPEG, PNG, GIF)"
	}

	// Check file extension
	filename := file.Filename
	ext := strings.ToLower(filepath.Ext(filename))
	if ext != ".jpg" && ext != ".jpeg" && ext != ".png" && ext != ".gif" {
		return false, "Invalid file extension (only .jpg, .jpeg, .png, .gif are allowed)"
	}

	return true, ""
}

// GenerateUniqueID generates a unique ID for image naming
func GenerateUniqueID() (string, error) {
	bytes := make([]byte, 16)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return hex.EncodeToString(bytes), nil
} 