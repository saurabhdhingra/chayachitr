FROM golang:1.21-alpine AS builder

# Set working directory
WORKDIR /app

# Install required dependencies
RUN apk add --no-cache gcc musl-dev

# Copy go mod and sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy the source code
COPY . .

# Build the application
RUN CGO_ENABLED=1 GOOS=linux go build -a -o chayachitr .

# Use a smaller image for the final build
FROM alpine:latest

# Install required dependencies
RUN apk add --no-cache ca-certificates tzdata

# Set working directory
WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /app/chayachitr .

# Copy .env file
COPY .env .

# Expose port
EXPOSE 8080

# Run the application
CMD ["./chayachitr"] 