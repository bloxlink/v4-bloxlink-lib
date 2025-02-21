from abc import ABC, abstractmethod
from enum import Enum
from bloxlink_lib.models.base import BaseModel


class DatabaseDomains(Enum):
    """All database domains available in Bloxlink."""

    USERS = "users"
    GUILDS = "guilds"
    V4_MIGRATOR_ERROR_LOGS = "v4_schema_error_log"


class BaseSchema(BaseModel, ABC):
    """Base schema for all schemas to inherit from."""

    @staticmethod
    @abstractmethod
    def database_domain() -> Enum:
        """The database domain for the schema."""


from .guilds import *
from .users import *
