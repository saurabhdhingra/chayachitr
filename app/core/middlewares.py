import time
from collections import defaultdict
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

# Import the function that determines the user ID (which we just created)
from app.api.deps import get_current_user_id

# --- Configuration for Rate Limiting ---
MAX_REQUESTS = 5      # Maximum number of requests allowed
TIME_WINDOW = 60      # Time window in seconds (5 requests per minute)

# In-memory store for tracking requests. 
# WARNING: This is volatile. For production, replace with Redis or similar.
RATE_LIMIT_STORE = defaultdict(lambda: {"count": 0, "first_request_time": 0.0})

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Implements a simple, in-memory rate limiting mechanism.

    It identifies the client first by authenticated user ID (if available)
    and falls back to using the client's IP address.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.max_requests = MAX_REQUESTS
        self.time_window = TIME_WINDOW

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        
        # 1. Determine the Client ID for rate limiting
        
        # Try to get the authenticated user ID (None if unauthenticated)
        client_id: Optional[str] = await get_current_user_id(request)
        
        if client_id is None:
            # Fallback to IP address if the user is not authenticated
            # Checks for X-Forwarded-For (for use behind proxies/load balancers)
            client_ip = request.headers.get("x-forwarded-for") or request.client.host
            client_id = client_ip

        # 2. Check and enforce the rate limit
        
        now = time.time()
        record = RATE_LIMIT_STORE[client_id]

        # Check if the time window has passed. If so, reset the count.
        if now - record["first_request_time"] > self.time_window:
            record["count"] = 1
            record["first_request_time"] = now
        else:
            record["count"] += 1

            if record["count"] > self.max_requests:
                # Rate limit exceeded (HTTP 429 Too Many Requests)
                return JSONResponse(
                    {"detail": f"Rate limit exceeded for client '{client_id}'. Try again in {self.time_window} seconds."},
                    status_code=429,
                )

        # 3. Proceed to the next middleware or endpoint
        response = await call_next(request)
        
        # 4. Add Rate Limit headers for client information
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.max_requests - record["count"]))
        
        # Calculate when the window resets
        reset_time = int(record["first_request_time"] + self.time_window)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response