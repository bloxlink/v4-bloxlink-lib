from typing import Any
from bloxlink_lib.models.base import BaseModel


class BasePayload(BaseModel):
    """Base payload model."""


class BaseResponse[T: Any](BaseModel):
    """Base response model."""

    success: bool
    error: str | None = None
    data: T | None = None
