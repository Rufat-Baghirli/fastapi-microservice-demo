from fastapi import HTTPException, status
from typing import Any

class AppException(HTTPException):
    """
    Base application exception that wraps HTTPException for consistency.
    Use subclasses for domain-specific errors.
    """
    def __init__(self, status_code: int, detail: Any):
        super().__init__(status_code=status_code, detail=detail)


class BadRequestException(AppException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedException(AppException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenException(AppException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictException(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InternalServerError(AppException):
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


# Domain / business exceptions
class UserNotFound(NotFoundException):
    def __init__(self, user_id: int | None = None):
        detail = f"User with ID {user_id} not found" if user_id else "User not found"
        super().__init__(detail=detail)


class InvalidCredentials(UnauthorizedException):
    def __init__(self):
        super().__init__(detail="Invalid email or password")
