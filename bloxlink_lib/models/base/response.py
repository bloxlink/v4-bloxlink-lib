from typing import Any
from bloxlink_lib.models.base import BaseModel


class Response[T: Any](BaseModel):
    """Base response model."""

    success: bool
    error: str | None = None
    data: T | None = None
