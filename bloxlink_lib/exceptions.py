class BloxlinkException(Exception):
    """Base exception for Bloxlink."""

    def __init__(
        self,
        error: str | None = None,
        ephemeral: bool = False,
        status_code: int | None = None,
    ) -> None:
        self.error = error  # used by both the bot and web components
        self.ephemeral = ephemeral  # used by the bot component
        self._status_code = status_code  # used by the web component

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
