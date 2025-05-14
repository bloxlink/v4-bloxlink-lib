from http import HTTPStatus


class BloxlinkException(Exception):
    """Base exception for Bloxlink."""

    def __init__(
        self,
        message: str | None = None,
        *,
        send_ephemeral: bool = False,
        status_code: int = HTTPStatus.BAD_REQUEST,
    ):
        self.message = message or "An unexpected error occurred."
        self.send_ephemeral = send_ephemeral  # Used exclusively by the bot to send the message as an ephemeral message. Not shown in web responses.
        self.status_code = status_code  # If this is used by a web component, this will be the status code used.

        super().__init__(message)


class Message(BloxlinkException):
    """Generic exception to communicate some message to the user. Not necessarily an error."""

    status_code = HTTPStatus.OK


# ERRORS
class Error(BloxlinkException):
    """Generic error."""

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR


class RobloxNotFound(Error):
    """Raised when a Roblox entity is not found."""

    status_code = HTTPStatus.NOT_FOUND


class RobloxAPIError(Error):
    """Raised when the Roblox API returns an error."""

    status_code = HTTPStatus.BAD_REQUEST


class RobloxDown(Error):
    """Raised when the Roblox API is down."""

    status_code = HTTPStatus.SERVICE_UNAVAILABLE


class UserNotVerified(Error):
    """Raised when a user is not verified."""

    status_code = HTTPStatus.FORBIDDEN


class BloxlinkForbidden(Error):
    """Raised when a user lacks permissions."""

    status_code = HTTPStatus.FORBIDDEN
