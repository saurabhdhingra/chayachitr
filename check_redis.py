import os
from dotenv import load_dotenv
import redis

# 1. Load the environment variables from your .env file
load_dotenv() 

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT", 6379) # Use 6379 as default if not found

print(f"Attempting to connect to Redis at {REDIS_HOST}:{REDIS_PORT}...")

try:
    # Initialize the Redis client
    r = redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        db=0,
        socket_connect_timeout=5 # Set a timeout
    )
    
    # 2. Execute the PING command to test the connection
    r.ping()
    
    print("\n✅ SUCCESS: Redis server is running and connected to the application!")
    
    # Optional: Test reading/writing a key
    r.set("app:test_key", "connection_successful")
    test_value = r.get("app:test_key")
    print(f"Test key written and read successfully. Value: {test_value.decode()}")

except redis.exceptions.ConnectionError as e:
    print("\n❌ ERROR: Failed to connect to Redis.")
    print(f"Details: {e}")
    print("\nTroubleshooting Steps:")
    print("1. Ensure your Docker Redis container is running.")
    print("2. Check that the REDIS_HOST and REDIS_PORT in your .env are correct.")
    print("3. Verify the Redis port (6379) is not blocked by a firewall.")
    
except Exception as e:
    print(f"An unexpected error occurred: {e}")