package config

import (
	"context"
	"os"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
	"go.mongodb.org/mongo-driver/mongo/readpref"
)

// Database represents the MongoDB client and database
type Database struct {
	Client *mongo.Client
	DB     *mongo.Database
}

// ConnectDB establishes a connection to MongoDB
func ConnectDB() (*Database, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Get MongoDB URI from environment variables
	mongoURI := os.Getenv("MONGO_URI")
	if mongoURI == "" {
		mongoURI = "mongodb://localhost:27017"
	}

	// Create MongoDB client
	client, err := mongo.Connect(ctx, options.Client().ApplyURI(mongoURI))
	if err != nil {
		return nil, err
	}

	// Ping the database to verify connection
	if err := client.Ping(ctx, readpref.Primary()); err != nil {
		return nil, err
	}

	// Get database name from environment variables
	dbName := os.Getenv("DB_NAME")
	if dbName == "" {
		dbName = "chayachitr"
	}

	// Get the database
	db := client.Database(dbName)

	return &Database{
		Client: client,
		DB:     db,
	}, nil
}

// Close disconnects from MongoDB
func (d *Database) Close() error {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	return d.Client.Disconnect(ctx)
}

// GetCollection returns a MongoDB collection
func (d *Database) GetCollection(name string) *mongo.Collection {
	return d.DB.Collection(name)
} 