package middleware

import (
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

// RateLimiter implements a simple in-memory rate limiter
type RateLimiter struct {
	sync.Mutex
	requests   map[string][]time.Time
	limit      int
	windowSecs int
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(limit, windowSecs int) *RateLimiter {
	return &RateLimiter{
		requests:   make(map[string][]time.Time),
		limit:      limit,
		windowSecs: windowSecs,
	}
}

// RateLimiterMiddleware creates a middleware for rate limiting
func RateLimiterMiddleware(limit, windowSecs int) gin.HandlerFunc {
	limiter := NewRateLimiter(limit, windowSecs)

	return func(c *gin.Context) {
		ip := c.ClientIP()
		
		limiter.Lock()
		defer limiter.Unlock()

		now := time.Now()
		
		// Initialize if this is the first request from this IP
		if _, exists := limiter.requests[ip]; !exists {
			limiter.requests[ip] = []time.Time{}
		}

		// Filter out requests older than the window
		var validRequests []time.Time
		windowStart := now.Add(-time.Duration(limiter.windowSecs) * time.Second)
		
		for _, requestTime := range limiter.requests[ip] {
			if requestTime.After(windowStart) {
				validRequests = append(validRequests, requestTime)
			}
		}
		
		limiter.requests[ip] = validRequests

		// Check if the number of requests exceeds the limit
		if len(limiter.requests[ip]) >= limiter.limit {
			c.JSON(http.StatusTooManyRequests, gin.H{"error": "Rate limit exceeded"})
			c.Abort()
			return
		}

		// Add this request to the list
		limiter.requests[ip] = append(limiter.requests[ip], now)
		
		c.Next()
	}
} 