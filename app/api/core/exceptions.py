from fastapi import HTTPException, status

class ServiceException(HTTPException):
    """Base exception for all domain/service errors that map to HTTP status codes."""
    pass

class UserNotFound(ServiceException):
    def __init__(self, detail: str = "User not found."):
        super().__init__(status_code = status.HTTP_404_NOT_FOUND, detail=detail)

class InvalidCredentials(ServiceException):
    def __init__(self, detail: str = "Incorrect username or password."):
        super().__init__(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = detail, 
            headers = {"WWW-Authenticate": "Bearer"}
        )


class ImageNotFoundError(ServiceException):
    def __init__(self, detail: str = "Image not found or access denied."):
        super().__init__(status_code = status.HTTP_404_NOT_FOUND, detail = detail)
        
class TransformationError(ServiceException):
    def __init__(self, detail: str = "Failed to apply one or more transformations."):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)

class RegistrationError(ServiceException):
    def __init__(self, detail: str = "Username already exists."):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)