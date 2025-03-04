class BloxlinkException(Exception):
    """Base exception for Bloxlink."""

    def __init__(self, error: str | None = None, ephemeral: bool = False):
        self.error = error
        self.ephemeral = ephemeral

    def __str__(self) -> str:
        return self.error or "An error occurred."


class RobloxNotFound(BloxlinkException):
    """Raised when a Roblox entity is not found."""


class RobloxAPIError(BloxlinkException):
    """Raised when the Roblox API returns an error."""


class RobloxDown(BloxlinkException):
    """Raised when the Roblox API is down."""


class UserNotVerified(BloxlinkException):
    """Raised when a user is not verified."""


class Message(BloxlinkException):
    """Generic exception to communicate some message to the user."""


class Error(Message):
    """Generic user-thrown error."""
