package utils

import (
	"bytes"
	"image"
	"image/color"
	"image/draw"
	"image/jpeg"
	"image/png"
	"io"

	"github.com/disintegration/imaging"
	"golang.org/x/image/font"
	"golang.org/x/image/font/basicfont"
	"golang.org/x/image/math/fixed"
)

// AddWatermark adds a text watermark to an image
func AddWatermark(img image.Image, text string, x, y int, opacity float64) image.Image {
	// Create a new RGBA image
	bounds := img.Bounds()
	rgba := image.NewRGBA(bounds)
	draw.Draw(rgba, bounds, img, bounds.Min, draw.Src)

	// Set up the font drawer
	d := &font.Drawer{
		Dst:  rgba,
		Src:  image.NewUniform(color.RGBA{R: 255, G: 255, B: 255, A: uint8(opacity * 255)}),
		Face: basicfont.Face7x13,
		Dot:  fixed.Point26_6{X: fixed.Int26_6(x * 64), Y: fixed.Int26_6(y * 64)},
	}

	// Draw the text
	d.DrawString(text)

	return rgba
}

// ApplySepia applies a sepia filter to an image
func ApplySepia(img image.Image) image.Image {
	bounds := img.Bounds()
	sepia := image.NewRGBA(bounds)

	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			r, g, b, a := img.At(x, y).RGBA()
			r >>= 8
			g >>= 8
			b >>= 8
			a >>= 8

			// Apply sepia formula
			tr := float64(r)*0.393 + float64(g)*0.769 + float64(b)*0.189
			tg := float64(r)*0.349 + float64(g)*0.686 + float64(b)*0.168
			tb := float64(r)*0.272 + float64(g)*0.534 + float64(b)*0.131

			// Clamp values
			if tr > 255 {
				tr = 255
			}
			if tg > 255 {
				tg = 255
			}
			if tb > 255 {
				tb = 255
			}

			sepia.Set(x, y, color.RGBA{uint8(tr), uint8(tg), uint8(tb), uint8(a)})
		}
	}

	return sepia
}

// CompressJPEG compresses a JPEG image with the specified quality
func CompressJPEG(img image.Image, quality int) ([]byte, error) {
	var buf bytes.Buffer
	err := jpeg.Encode(&buf, img, &jpeg.Options{Quality: quality})
	if err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// CompressPNG compresses a PNG image
func CompressPNG(img image.Image) ([]byte, error) {
	var buf bytes.Buffer
	err := png.Encode(&buf, img)
	if err != nil {
		return nil, err
	}
	return buf.Bytes(), nil
}

// DecodeImage decodes an image from an io.Reader
func DecodeImage(r io.Reader) (image.Image, error) {
	img, _, err := image.Decode(r)
	if err != nil {
		return nil, err
	}
	return img, nil
}

// GetImageFormat determines the image format from a filename
func GetImageFormat(filename string) (format imaging.Format) {
	switch {
	case hasExtension(filename, ".jpg", ".jpeg"):
		format = imaging.JPEG
	case hasExtension(filename, ".png"):
		format = imaging.PNG
	case hasExtension(filename, ".gif"):
		format = imaging.GIF
	case hasExtension(filename, ".bmp"):
		format = imaging.BMP
	case hasExtension(filename, ".tif", ".tiff"):
		format = imaging.TIFF
	default:
		format = imaging.JPEG
	}
	return
}

// hasExtension checks if a filename has any of the provided extensions
func hasExtension(filename string, extensions ...string) bool {
	for _, ext := range extensions {
		if len(filename) >= len(ext) && filename[len(filename)-len(ext):] == ext {
			return true
		}
	}
	return false
} 