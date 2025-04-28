package routes

import (
	"github.com/gin-gonic/gin"
	"github.com/yourname/chayachitr/config"
	"github.com/yourname/chayachitr/controllers"
	"github.com/yourname/chayachitr/middleware"
	"github.com/yourname/chayachitr/storage"
	"net/http"
	"os"
)

// SetupRouter sets up the routes for the application
func SetupRouter(db *config.Database, storageClient *storage.StorageClient) *gin.Engine {
	// Set Gin mode based on environment variable
	env := os.Getenv("ENV")
	if env == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	// Create a new Gin router
	router := gin.Default()

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "UP",
			"info": gin.H{
				"database": "UP",
				"storage":  "UP",
			},
		})
	})

	// Create controllers
	authController := controllers.NewAuthController(db)
	imageController := controllers.NewImageController(db, storageClient)

	// Public routes
	router.POST("/register", authController.Register)
	router.POST("/login", authController.Login)

	// Protected routes
	protected := router.Group("/")
	protected.Use(middleware.AuthMiddleware())
	{
		// Image routes
		protected.POST("/images", imageController.UploadImage)
		protected.GET("/images/:id", imageController.GetImage)
		protected.GET("/images", imageController.ListImages)
		
		// Apply rate limiting to transformation endpoint (100 requests per hour)
		transformGroup := protected.Group("/")
		transformGroup.Use(middleware.RateLimiterMiddleware(100, 3600))
		transformGroup.POST("/images/:id/transform", imageController.TransformImage)
	}

	return router
} 