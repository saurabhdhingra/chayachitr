from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import REDISfrom app.core.config import settings

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Implements rate limiting using Redis based on the client's IP address.
    """

    def __init__(self, app):
        super().__init__(app)

        try: 
            limit_str, period_str = settings.RATE_LIMIT.split('/')
            self.limit = int(limit_str)

            if period_str == 'minute':
                self.period = 60
            elif period_str == 'hour':
                self.period = 3600
            else:
                raise ValueError(f"Unsupported rate limit period: {period_str}")

        except (ValueError, IndexError):
            print(f"FATAL: Invalid RATE_LIMIT format: {settings.RATE_LIMIT}. Rate limiting disabled.")
            self.redis_client = None
            return

        try :
            self.redis_client = redis.StrictRedis(
                host = settings.REDIS_HOST, 
                port = settings.REDIS_PORT,
                decode_response = True
            )
            self.redis_client.ping()
            print("Redis connection successful. Rate Limiting enabled.")
        except redis.exceptions.ConnectionError as e: 
            print(f"WARNING: Redis connection failed at {settings.REDIS_HOST}:{settings.REDIS_PORT}. Rate limiting will be disabled. Error: {e}")
            self.redis_client = None

    async def dispatch(self, request: Request, call_next):
        """
        Applies rate limiting using the Redis counter pattern.
        """

        if self.redis_client is None:
            return await call_next(request)

        if request.url.path.endswith("/transform") and requst.method == "POST":
            return await call_next(request)

        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"

        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.period, nx = True)

        try:
            count, _ = pipe.execute()
        expect Exception as e:
            print(f"Redis pipeline execution failed, skipping rate limit check. Error: {e}")
            return await call_next(request)

        if count > self.limit:
            ttl = self.redis_client.ttl(key)
            if ttl < 0:
                ttl = self.period

            raise HTTPException(
                status_code = status.HTTP_429_TOO_MANY_REQUESTS,
                detail = f"Rate limit exceeded. Try again in {ttl} seconds.",
                headers = {"Retry-After": str(ttl)}
            )
        
        response = await call_next(request)
        return response
     