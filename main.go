package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/joho/godotenv"
	"github.com/yourname/chayachitr/config"
	"github.com/yourname/chayachitr/routes"
	"github.com/yourname/chayachitr/storage"
)

func main() {
	// Load environment variables
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using system environment variables")
	}

	// Initialize database connection
	db, err := config.ConnectDB()
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}

	// Initialize storage client based on configuration
	var storageClient storage.StorageInterface
	storageType := os.Getenv("STORAGE_TYPE")
	if storageType == "s3" {
		storageClient, err = storage.NewS3Client()
		if err != nil {
			log.Fatalf("Failed to initialize S3 storage client: %v", err)
		}
		log.Println("Using AWS S3 as storage provider")
	} else {
		storageClient, err = storage.NewMinioClient()
		if err != nil {
			log.Fatalf("Failed to initialize MinIO storage client: %v", err)
		}
		log.Println("Using MinIO as storage provider")
	}

	// Initialize and start the server
	server := routes.SetupRouter(db, storageClient)
	
	// Start server in a goroutine
	go func() {
		port := os.Getenv("PORT")
		if port == "" {
			port = "8080"
		}
		
		if err := server.Run(":" + port); err != nil {
			log.Fatalf("Failed to start server: %v", err)
		}
	}()
	
	// Wait for interrupt signal to gracefully shutdown the server
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	
	log.Println("Shutting down server...")
	
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	
	if err := server.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}
	
	log.Println("Server exiting")
} 