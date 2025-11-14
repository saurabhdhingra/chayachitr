import redis
from app.core.config import settings
from typing import Optional

class RedisAdapter:
    """
    Adapter for all Redis interactions, including caching and rate limiting.
    Initializes a connection pool and provides simple GET/SET/INCR operations.
    """
    def __init__(self):
        self._client: Optional[redis.StrictRedis] = None
        
        try:
            self._client = redis.StrictRedis(
                host=settings.REDIS_HOST, 
                port=settings.REDIS_PORT, 
                decode_responses=True
            )
            self._client.ping()
            print("Redis Adapter: Connection successful.")
        except redis.exceptions.ConnectionError as e:
            print(f"WARNING: Redis connection failed at {settings.REDIS_HOST}:{settings.REDIS_PORT}. Redis functionality disabled. Error: {e}")
            self._client = None
            
    def is_available(self) -> bool:
        return self._client is not None
        
    def get_client(self) -> redis.StrictRedis:
        if not self.is_available():
            raise ConnectionError("Redis client is not initialized or available.")
        return self._client

    def get(self, key: str) -> Optional[str]:
        """Retrieves a value by key."""
        if not self.is_available(): return None
        try:
            return self._client.get(key)
        except Exception as e:
            print(f"Redis GET error for key {key}: {e}")
            return None

    def set(self, key: str, value: str, ttl: int) -> bool:
        """Sets a key-value pair with a Time-To-Live (TTL) in seconds."""
        if not self.is_available(): return False
        try:
            return self._client.setex(key, ttl, value)
        except Exception as e:
            print(f"Redis SET error for key {key}: {e}")
            return False
            
    def incr_and_expire(self, key: str, period: int) -> Optional[int]:
        """Atomically increments a key and sets its expiration if it's new. Returns the new count."""
        if not self.is_available(): return None
        try:
            pipe = self._client.pipeline()
            pipe.incr(key)
            # NX=True ensures EXPIRY is only set on the FIRST increment
            pipe.expire(key, period, nx=True) 
            count, _ = pipe.execute() 
            return count
        except Exception as e:
            print(f"Redis INCR/EXPIRE pipeline failed for key {key}: {e}")
            return None

    def ttl(self, key: str) -> Optional[int]:
        """Returns the remaining time to live of a key in seconds."""
        if not self.is_available(): return None
        try:
            return self._client.ttl(key)
        except Exception as e:
            print(f"Redis TTL error for key {key}: {e}")
            return None