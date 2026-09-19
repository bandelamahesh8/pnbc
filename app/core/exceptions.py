from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None,
        error_type: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details
        self.error_type = error_type or self.__class__.__name__


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
            error_type="NotFound"
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Could not validate credentials", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            error_type="Unauthorized"
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Not enough permissions", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
            error_type="Forbidden"
        )


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            error_type="ValidationError"
        )


class FileValidationException(AppException):
    def __init__(self, message: str = "Invalid file", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            error_type="FileValidationError"
        )


class ProcessingException(AppException):
    def __init__(self, message: str = "Document processing failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            error_type="ProcessingError"
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_type,
                "message": exc.message,
                "details": exc.details,
                "status_code": exc.status_code
            }
        )
