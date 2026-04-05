from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .api_response import ApiResponse
from .logger import logger


class AppException(Exception):
    def __init__(self, message: str, code: int = -1):
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message=message, code=404)


class ValidationException(AppException):
    def __init__(self, message: str = "参数校验失败"):
        super().__init__(message=message, code=422)


class LLMException(AppException):
    def __init__(self, message: str = "LLM 服务调用失败"):
        super().__init__(message=message, code=502)


class DatabaseException(AppException):
    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(message=message, code=500)


# HTTP status code 映射
_STATUS_CODE_MAP = {404: 404, 422: 422, 502: 502, 500: 500}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException):
        status_code = _STATUS_CODE_MAP.get(exc.code, 400)
        logger.warning("业务异常: [%d] %s", exc.code, exc.message)
        return JSONResponse(
            status_code=status_code,
            content=ApiResponse.error(message=exc.message, code=exc.code).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(_request: Request, exc: Exception):
        logger.error("未处理异常: %s", str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ApiResponse.error(
                message="服务器内部错误，请稍后重试", code=500
            ).model_dump(),
        )
