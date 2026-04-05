from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api_response import ApiResponse


class AppException(Exception):
    def __init__(self, message: str, code: int = -1):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, code=404)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, code=422)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException):
        return JSONResponse(
            status_code=200,
            content=ApiResponse.error(message=exc.message, code=exc.code).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(_request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(
                message=f"Internal server error: {str(exc)}", code=500
            ).model_dump(),
        )
