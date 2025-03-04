from http import HTTPStatus as StatusCodes


class BloxlinkException(Exception):
    """Base exception for Bloxlink."""

    def __init__(
        self,
        message: str | None = None,
        ephemeral: bool = False,
        status_code: int | None = None,
    ) -> None:
        self.message = message  # used by both the bot and web components
        self.ephemeral = ephemeral  # used by the bot component
        self.status_code = status_code  # used by the web component

    def __str__(self) -> str:
        return self.message or "An error occurred."


class Error(BloxlinkException):
    """Generic user-thrown error."""

    def __init__(
        self,
        error: str | None = None,
        ephemeral: bool = False,
        status_code: int | None = StatusCodes.BAD_REQUEST,
    ) -> None:
        super().__init__(message=error, ephemeral=ephemeral, status_code=status_code)


class RobloxNotFound(Error):
    """Raised when a Roblox entity is not found."""


class RobloxAPIError(Error):
    """Raised when the Roblox API returns an error."""


class RobloxDown(Error):
    """Raised when the Roblox API is down."""


class UserNotVerified(Error):
    """Raised when a user is not verified."""


class Message(BloxlinkException):
    """Generic exception to communicate some message to the user. Not necessarily an error."""

    def __init__(
        self,
        message: str | None = None,
        ephemeral: bool = False,
        status_code: int | None = StatusCodes.OK,
    ) -> None:
        super().__init__(message, ephemeral, status_code)
