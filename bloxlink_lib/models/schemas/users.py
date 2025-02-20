from pydantic import Field
from bloxlink_lib.database.mongodb import (  # pylint: disable=no-name-in-module
    fetch_item,
    update_item,
)
from bloxlink_lib.models.schemas import BaseSchema, DatabaseDomains
from bloxlink_lib.models.base.serializable import MemberSerializable


class UserData(BaseSchema):
    """Representation of a User's data in Bloxlink

    Attributes:
        id (int): The Discord ID of the user.
        robloxID (str): The roblox ID of the user's primary account.
        robloxAccounts (dict): All of the user's linked accounts, and any guild specific verifications.
    """

    id: int
    robloxID: str | None = None
    robloxAccounts: dict = Field(
        default_factory=lambda: {"accounts": [], "guilds": {}, "confirms": {}}
    )

    @staticmethod
    def database_domain() -> DatabaseDomains:
        """The database domain for the schema."""

        return DatabaseDomains.USERS


async def fetch_user_data(
    user: str | int | dict | MemberSerializable, *aspects
) -> UserData:
    """
    Fetch a full user from local cache, then redis, then database.
    Will populate caches for later access
    """

    if isinstance(user, dict):
        user_id = str(user["id"])
    elif isinstance(user, MemberSerializable):
        user_id = str(user.id)
    else:
        user_id = str(user)

    return await fetch_item("users", UserData, user_id, *aspects)


async def update_user_data(
    user: str | int | dict | MemberSerializable, **aspects
) -> None:
    """
    Update a user's aspects in local cache, redis, and database.
    """

    if isinstance(user, dict):
        user_id = str(user["id"])
    elif isinstance(user, MemberSerializable):
        user_id = str(user.id)
    else:
        user_id = str(user)

    return await update_item(UserData, user_id, **aspects)
