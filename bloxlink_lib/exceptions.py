class BloxlinkException(Exception):
    """Base exception for Bloxlink."""

    def __init__(self, message: str, send_ephemeral: bool = False):
        self.message = message
        self.send_ephemeral = send_ephemeral  # Used exclusively by the bot to send the message as an ephemeral message. Not shown in web responses.

        super().__init__(message)


class Message(BloxlinkException):
    """Generic exception to communicate some message to the user. Not necessarily an error."""


# ERRORS
class Error(BloxlinkException):
    """Generic error."""


class RobloxNotFound(Error):
    """Raised when a Roblox entity is not found."""


class RobloxAPIError(Error):
    """Raised when the Roblox API returns an error."""


class RobloxDown(Error):
    """Raised when the Roblox API is down."""


class UserNotVerified(Error):
    """Raised when a user is not verified."""


class BloxlinkForbidden(Error):
    """Raised when a user lacks permissions."""
