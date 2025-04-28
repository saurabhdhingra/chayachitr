package models

import (
	"time"

	"go.mongodb.org/mongo-driver/bson/primitive"
)

// Image represents an image stored in the system
type Image struct {
	ID           primitive.ObjectID  `bson:"_id,omitempty" json:"id,omitempty"`
	UserID       primitive.ObjectID  `bson:"user_id" json:"user_id"`
	Filename     string              `bson:"filename" json:"filename"`
	ContentType  string              `bson:"content_type" json:"content_type"`
	Size         int64               `bson:"size" json:"size"`
	ObjectName   string              `bson:"object_name" json:"object_name"`
	URL          string              `bson:"url" json:"url"`
	Transformations []*Transformation `bson:"transformations" json:"transformations"`
	CreatedAt    time.Time           `bson:"created_at" json:"created_at"`
	UpdatedAt    time.Time           `bson:"updated_at" json:"updated_at"`
}

// Transformation represents an image transformation
type Transformation struct {
	ID           primitive.ObjectID `bson:"_id,omitempty" json:"id,omitempty"`
	ImageID      primitive.ObjectID `bson:"image_id" json:"image_id"`
	ObjectName   string             `bson:"object_name" json:"object_name"`
	URL          string             `bson:"url" json:"url"`
	Parameters   TransformParams    `bson:"parameters" json:"parameters"`
	Hash         string             `bson:"hash" json:"hash"`
	CreatedAt    time.Time          `bson:"created_at" json:"created_at"`
}

// TransformParams represents transformation parameters
type TransformParams struct {
	Resize   *ResizeParams   `bson:"resize,omitempty" json:"resize,omitempty"`
	Crop     *CropParams     `bson:"crop,omitempty" json:"crop,omitempty"`
	Rotate   *float64        `bson:"rotate,omitempty" json:"rotate,omitempty"`
	Format   *string         `bson:"format,omitempty" json:"format,omitempty"`
	Filters  *FilterParams   `bson:"filters,omitempty" json:"filters,omitempty"`
	Flip     *bool           `bson:"flip,omitempty" json:"flip,omitempty"`
	Mirror   *bool           `bson:"mirror,omitempty" json:"mirror,omitempty"`
	Watermark *WatermarkParams `bson:"watermark,omitempty" json:"watermark,omitempty"`
	Quality  *int            `bson:"quality,omitempty" json:"quality,omitempty"`
}

// ResizeParams represents resize parameters
type ResizeParams struct {
	Width  int `bson:"width" json:"width"`
	Height int `bson:"height" json:"height"`
}

// CropParams represents crop parameters
type CropParams struct {
	Width  int `bson:"width" json:"width"`
	Height int `bson:"height" json:"height"`
	X      int `bson:"x" json:"x"`
	Y      int `bson:"y" json:"y"`
}

// FilterParams represents filter parameters
type FilterParams struct {
	Grayscale bool `bson:"grayscale" json:"grayscale"`
	Sepia     bool `bson:"sepia" json:"sepia"`
	Blur      *float64 `bson:"blur,omitempty" json:"blur,omitempty"`
	Sharpen   *float64 `bson:"sharpen,omitempty" json:"sharpen,omitempty"`
}

// WatermarkParams represents watermark parameters
type WatermarkParams struct {
	Text     string `bson:"text" json:"text"`
	FontSize float64 `bson:"font_size" json:"font_size"`
	X        int     `bson:"x" json:"x"`
	Y        int     `bson:"y" json:"y"`
	Opacity  float64 `bson:"opacity" json:"opacity"`
}

// ImageListResponse represents the response for image listing
type ImageListResponse struct {
	Images      []Image `json:"images"`
	TotalCount  int64   `json:"total_count"`
	PageSize    int64   `json:"page_size"`
	CurrentPage int64   `json:"current_page"`
	TotalPages  int64   `json:"total_pages"`
} 