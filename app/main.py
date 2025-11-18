from fastapi import FastAPI
from app.api.v1.endpoints import auth, images
from app.core.config import settings
from app.core.middlewares import RateLimiterMiddleware

def get_application() -> FastAPI:
    application = FastAPI(
        title = settings.PROJECT_NAME,
        version = "0.1.0",
        docs_url = "/docs"
    )

    # Note: RateLimiterMiddleware should typically be imported and instantiated 
    # from starlette.middleware.base or similar, depending on its implementation.
    application.add_middleware(RateLimiterMiddleware)

    application.include_router(
        auth.router,
        prefix = f"{settings.API_V1_STR}", # <-- REQUIRED COMMA ADDED HERE
        tags = ["Authentication"] 
    )

    application.include_router(
        images.router, 
        prefix = f"{settings.API_V1_STR}/images", # <-- REQUIRED COMMA ADDED HERE
        tags = ["Image Management"]
    )

    return application

app = get_application()