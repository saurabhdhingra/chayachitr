package middleware

import (
	"fmt"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/dgrijalva/jwt-go"
	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

// JWTClaims represents JWT claims
type JWTClaims struct {
	UserID string `json:"user_id"`
	jwt.StandardClaims
}

// GenerateToken generates a JWT token for a user
func GenerateToken(userID primitive.ObjectID) (string, error) {
	// Get JWT secret from environment variables
	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		jwtSecret = "default_secret_key_replace_in_production"
	}

	// Get JWT expiration from environment variables
	jwtExpirationStr := os.Getenv("JWT_EXPIRATION")
	if jwtExpirationStr == "" {
		jwtExpirationStr = "24h"
	}

	// Parse JWT expiration
	jwtExpiration, err := time.ParseDuration(jwtExpirationStr)
	if err != nil {
		jwtExpiration = 24 * time.Hour
	}

	// Create claims with expiration time
	claims := JWTClaims{
		UserID: userID.Hex(),
		StandardClaims: jwt.StandardClaims{
			ExpiresAt: time.Now().Add(jwtExpiration).Unix(),
			IssuedAt:  time.Now().Unix(),
		},
	}

	// Create token with claims
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)

	// Sign the token with the secret key
	tokenString, err := token.SignedString([]byte(jwtSecret))
	if err != nil {
		return "", err
	}

	return tokenString, nil
}

// AuthMiddleware authenticates requests using JWT
func AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Get authorization header
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header is required"})
			c.Abort()
			return
		}

		// Extract the token from the authorization header
		parts := strings.Split(authHeader, "Bearer ")
		if len(parts) != 2 {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header format must be Bearer {token}"})
			c.Abort()
			return
		}

		tokenString := parts[1]

		// Get JWT secret from environment variables
		jwtSecret := os.Getenv("JWT_SECRET")
		if jwtSecret == "" {
			jwtSecret = "default_secret_key_replace_in_production"
		}

		// Parse and validate the token
		token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
			// Validate the signing method
			if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
			}
			return []byte(jwtSecret), nil
		})

		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
			c.Abort()
			return
		}

		// Extract claims from the token
		if claims, ok := token.Claims.(*JWTClaims); ok && token.Valid {
			// Convert user ID from string to ObjectID
			userID, err := primitive.ObjectIDFromHex(claims.UserID)
			if err != nil {
				c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid user ID"})
				c.Abort()
				return
			}

			// Set user ID in context
			c.Set("user_id", userID)
			c.Next()
		} else {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid token"})
			c.Abort()
			return
		}
	}
} 