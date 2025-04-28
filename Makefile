.PHONY: build run clean test docker docker-compose

# Build the application
build:
	go build -o chayachitr .

# Run the application
run:
	go run main.go

# Clean the binary
clean:
	rm -f chayachitr

# Run tests
test:
	go test -v ./...

# Build docker image
docker:
	docker build -t chayachitr .

# Run docker-compose
docker-compose:
	docker-compose up -d

# Stop docker-compose
docker-compose-down:
	docker-compose down

# Show docker-compose logs
docker-compose-logs:
	docker-compose logs -f

# Initialize the project (download dependencies)
init:
	go mod download

# Format code
fmt:
	go fmt ./...

# Run linter
lint:
	golint ./... 