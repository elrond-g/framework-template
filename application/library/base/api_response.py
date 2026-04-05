from typing import Generic, TypeVar, Optional

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "ApiResponse[T]":
        return cls(code=0, message=message, data=data)

    @classmethod
    def error(cls, message: str, code: int = -1, data: T = None) -> "ApiResponse[T]":
        return cls(code=code, message=message, data=data)
