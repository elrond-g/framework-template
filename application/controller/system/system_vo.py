from pydantic import BaseModel


class HealthVO(BaseModel):
    status: str
    version: str
