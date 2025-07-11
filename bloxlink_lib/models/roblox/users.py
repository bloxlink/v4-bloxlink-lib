from __future__ import annotations

from typing import Annotated, Literal, TYPE_CHECKING
from pydantic import Field
import math
from http import HTTPStatus
from datetime import datetime
import hikari

from bloxlink_lib.models.schemas.users import (  # pylint: disable=no-name-in-module
    fetch_user_data,
)
from bloxlink_lib.fetch import fetch, fetch_typed
from bloxlink_lib.config import CONFIG
from bloxlink_lib.exceptions import RobloxNotFound, RobloxAPIError, UserNotVerified
from bloxlink_lib.database.mongodb import mongo  # pylint: disable=no-name-in-module
from bloxlink_lib.models.base import BaseModel, MemberSerializable, BaseResponse
from bloxlink_lib.utils import get_environment, Environment
from .groups import GroupRoleset, RobloxGroup

if TYPE_CHECKING:
    from .base_assets import RobloxBaseAsset

VALID_INFO_SERVER_SCOPES: list[Literal["groups", "badges"]] = ["groups", "badges"]
INVENTORY_API = "https://inventory.roblox.com"
USERS_API = "https://users.roblox.com"
USERS_BASE_DATA_API = USERS_API + "/v1/users/{roblox_id}"
USER_GROUPS_API = "https://groups.roblox.com/v2/users/{roblox_id}/groups/roles"
AVATAR_URLS = {
    "bustThumbnail": "https://thumbnails.roblox.com/v1/users/avatar-bust?userIds={roblox_id}&size=420x420&format=Png&isCircular=false",
    "headshotThumbnail": "https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={roblox_id}&size=420x420&format=Png&isCircular=false",
    "fullBody": "https://thumbnails.roblox.com/v1/users/avatar?userIds={roblox_id}&size=720x720&format=Png&isCircular=false",
}
BLOXLINK_VERIFICATION_URL = (
    "https://api.blox.link/v4/public/discord-to-roblox/{user_id}"
)


class BloxlinkVerificationResponse(BaseModel):
    """Type definition for a response from the public Bloxlink API."""

    robloxID: int | None = None
    error: str | None = None


class UserAvatar(BaseModel):
    """Type definition for a Roblox user's avatar from the Bloxlink Info API."""

    bust_thumbnail: str | None = Field(alias="bustThumbnail")
    headshot_thumbnail: str | None = Field(alias="headshotThumbnail")
    full_body: str | None = Field(alias="fullBody")


class RobloxUserAvatar(BaseModel):
    """Type definition for a Roblox avatar from the Roblox API."""

    target_id: int = Field(alias="targetId")
    state: str
    image_url: str = Field(alias="imageUrl")


class RobloxUserAvatarResponse(BaseModel):
    """Type definition for a Roblox user's avatar from the Roblox API."""

    data: list[RobloxUserAvatar]


class RobloxUserGroup(BaseModel):
    """Type definition for a Roblox group from a user from the Roblox API."""

    group: RobloxGroup
    role: GroupRoleset


class RobloxUserGroupResponse(BaseModel):
    """Type definition for a Roblox user's groups from the Roblox API."""

    data: list[RobloxUserGroup]


class RobloxUser(BaseModel):  # pylint: disable=too-many-instance-attributes
    """Representation of a user on Roblox."""

    # must provide one of these
    id: int | None = None
    username: str | None = Field(default=None, alias="name")

    # these fields are provided after sync() is called
    banned: bool = Field(alias="isBanned", default=False)
    age_days: int = None
    groups: dict[int, RobloxUserGroup] = Field(default_factory=dict)

    avatar: UserAvatar = None
    avatar_url: str | None = None

    description: str | None = None
    profile_link: str = Field(alias="profileLink", default=None)
    display_name: str | None = Field(alias="displayName", default=None)
    created: datetime = None
    short_age_string: str = None

    _complete: bool = False

    async def sync(
        self,
        includes: list[Literal["groups"]] | bool | None = None,
        *,
        cache: bool = True,
    ):
        """Retrieve and sync information about this user from Roblox. Requires a username or id to be set.

        Args:
            includes (list | bool | None, optional): Data that should be included. Defaults to None.
                True retrieves all available data; otherwise, a list can be passed with either
                "groups" in it.
            cache (bool, optional): Should we check the object for values before retrieving. Defaults to True.
        """

        if includes is None:
            includes = []

        elif includes is True:
            includes = VALID_INFO_SERVER_SCOPES
            self._complete = True

        if includes is not None and any(
            (x is False or x not in [*VALID_INFO_SERVER_SCOPES, True, None])
            for x in includes
        ):
            raise ValueError("Invalid includes provided.")

        if cache:
            # remove includes if we already have the value saved
            if self.groups and "groups" in includes:
                includes.remove("groups")

        roblox_user_data, user_data_response = await fetch_typed(
            RobloxUser,
            f"{CONFIG.BOT_API}/users",
            params={
                "id": self.id,
                "username": self.username,
                "include": ",".join(includes),
            },
        )

        if user_data_response.status == HTTPStatus.OK:
            self.id = roblox_user_data.id or self.id
            self.description = roblox_user_data.description or self.description
            self.username = roblox_user_data.username or self.username
            self.banned = roblox_user_data.banned or self.banned
            self.display_name = (
                roblox_user_data.display_name or self.display_name or self.username
            )
            self.created = (roblox_user_data.created or self.created).replace(
                tzinfo=None
            )
            self.avatar = roblox_user_data.avatar or self.avatar
            self.profile_link = roblox_user_data.profile_link or self.profile_link
            self.groups = roblox_user_data.groups or self.groups or {}

            self.parse_age()

            avatar = roblox_user_data.avatar

            if avatar:
                avatar_url, avatar_response = await fetch(
                    method="GET",
                    url=avatar.bust_thumbnail,
                    parse_as="JSON",
                )

                if avatar_response.status == HTTPStatus.OK:
                    self.avatar_url = (
                        avatar_url.get("data", [{}])[0].get("imageUrl") or None
                    )

    async def owns_asset(self, asset: RobloxBaseAsset) -> bool:
        """Check if the user owns a specific asset.

        Args:
            asset (RobloxBaseAsset): The asset to check for.

        Returns:
            bool: If the user owns the asset or not.
        """

        try:
            response_data, _ = await fetch(
                method="GET",
                url=f"{INVENTORY_API}/v1/users/{self.id}/items/{asset.type_number}/{asset.id}/is-owned",
                parse_as="TEXT",
            )
        except RobloxAPIError:
            return False

        return response_data == "true"

    def parse_age(self):
        """Set a human-readable string representing how old this account is."""
        if (self.age_days is not None) or not self.created:
            return

        today = datetime.now()
        self.age_days = (today - self.created).days

        if not self.short_age_string:
            if self.age_days >= 365:
                years = math.floor(self.age_days / 365)
                ending = f"yr{((years > 1 or years == 0) and 's') or ''}"
                self.short_age_string = f"{years} {ending} ago"
            else:
                ending = f"day{
                    ((self.age_days > 1 or self.age_days == 0) and 's') or ''}"
                self.short_age_string = f"{self.age_days} {ending} ago"


class RobloxUsernameData(BaseModel):
    requestedUsername: str
    hasVerifiedBadge: bool
    id: int
    name: str
    displayName: str


class RobloxUsernameResponse(BaseModel):
    data: list[RobloxUsernameData]


# fetch functions. these should not be used directly in commands; instead, get_user() should be used instead
async def fetch_roblox_id(roblox_username: str) -> int | None:
    """Fetch a Roblox ID from a Roblox username."""

    username_data, username_response = await fetch_typed(
        RobloxUsernameResponse,
        f"{USERS_API}/v1/usernames/users",
        method="POST",
        body={"usernames": [roblox_username], "excludeBannedUsers": False},
    )

    if username_response.status != HTTPStatus.OK:
        return None

    roblox_id = username_data.data[0].id if username_data.data else None

    return roblox_id


async def fetch_base_data(roblox_id: int) -> dict | None:
    """Fetch base data for a Roblox user."""

    user_base_data, user_base_data_response = await fetch_typed(
        RobloxUser,
        USERS_BASE_DATA_API.format(roblox_id=roblox_id),
        raise_on_failure=False,
    )

    if user_base_data_response.status != HTTPStatus.OK:
        return None

    return user_base_data.model_dump(exclude_unset=True)


async def fetch_user_groups(
    roblox_id: int,
) -> dict[Literal["groups"] : dict[int, RobloxUserGroup]] | None:
    """
    Fetch the groups of a user.

    This returns a dictionary with "groups" as the response
    so that this can be used with setattr() in the RobloxUser model.
    """

    user_groups, user_groups_response = await fetch_typed(
        RobloxUserGroupResponse,
        USER_GROUPS_API.format(roblox_id=roblox_id),
        raise_on_failure=False,
    )

    if user_groups_response.status != HTTPStatus.OK:
        return None

    return {
        "groups": {
            int(group_data.group.id): group_data for group_data in user_groups.data
        }
    }


async def fetch_user_avatars(
    roblox_id: int, resolve_avatars: bool
) -> dict[Literal["avatar"], UserAvatar]:
    """
    Fetch the avatar templates of a user.

    This returns a dictionary with "avatar" as the response
    so that this can be used with setattr() in the RobloxUser model.
    """

    avatars: dict = {}

    for avatar_name, avatar_url in AVATAR_URLS.items():
        if resolve_avatars:
            avatar_data, avatar_data_response = await fetch_typed(
                RobloxUserAvatarResponse,
                avatar_url.format(roblox_id=roblox_id),
                raise_on_failure=False,
            )
            if avatar_data_response.status == HTTPStatus.OK:
                avatars[avatar_name] = avatar_data.data[0].imageUrl
            else:
                avatars[avatar_name] = None
        else:
            avatars[avatar_name] = avatar_url.format(roblox_id=roblox_id)

    avatar_model = UserAvatar(**avatars)

    return {"avatar": avatar_model}


async def get_user_account(
    user: hikari.User | MemberSerializable | str,
    guild_id: int = None,
    raise_errors=True,
) -> RobloxUser | None:
    """Get a user's linked Roblox account.

    Args:
        user (hikari.User | str): The User or user ID to find the linked Roblox account for.
        guild_id (int, optional): Used to determine what account is linked in the given guild id.
            Defaults to None.
        raise_errors (bool, optional): Should errors be raised or not. Defaults to True.

    Raises:
        UserNotVerified: If raise_errors and user is not linked with Bloxlink.

    Returns:
        RobloxUser | None: The linked Roblox account either globally or for this guild, if any.
    """

    user_id = (
        str(user.id)
        if isinstance(user, (hikari.User, MemberSerializable))
        else str(user)
    )
    bloxlink_user = await fetch_user_data(user_id, "robloxID", "robloxAccounts")

    if guild_id:
        guild_accounts = (bloxlink_user.robloxAccounts or {}).get("guilds") or {}
        guild_account = guild_accounts.get(str(guild_id))

        if guild_account:
            return RobloxUser(id=guild_account)

    if bloxlink_user.robloxID:
        return RobloxUser(id=bloxlink_user.robloxID)

    # User is not verified in our database

    if CONFIG.STAGING_USE_FALLBACK_VERIFICATION_API and get_environment() in (
        Environment.STAGING,
        Environment.LOCAL,
    ):
        # Check production API if the user is verified
        response_body = (
            await fetch_typed(
                BloxlinkVerificationResponse,
                method="GET",
                url=BLOXLINK_VERIFICATION_URL.format(user_id=user_id),
                headers={"Authorization": CONFIG.BLOXLINK_PUBLIC_API_KEY},
                raise_on_failure=False,
            )
        )[0]

        if response_body.robloxID:
            return RobloxUser(id=response_body.robloxID)

    if raise_errors:
        raise UserNotVerified()

    return None


async def get_user(
    user: hikari.User | None = None,
    includes: list[Literal["groups", "badges"]] | None = None,
    *,
    roblox_username: str = None,
    roblox_id: int = None,
    guild_id: int = None,
    raise_on_unverified: bool = True,
) -> RobloxUser:
    """Get a Roblox account.

    If a user is not passed, it is required that either roblox_username OR roblox_id is given.

    guild_id only applies when a user is given.

    Args:
        user (hikari.User, optional): Get the account linked to this user. Defaults to None.
        includes (list | bool | None, optional): Data that should be included. Defaults to None.
            True retrieves all available data. Otherwise a list can be passed with either
            "groups", "presences", and/or "badges" in it.
        roblox_username (str, optional): Username of the account to get. Defaults to None.
        roblox_id (int, optional): ID of the account to get. Defaults to None.
        guild_id (int, optional): Guild ID if looking up a user to determine the linked account in that guild.
            Defaults to None.
        raise_on_unverified (bool, optional): Should an error be raised if the user is not verified? Defaults to True.
    Returns:
        RobloxUser | None: The found Roblox account, if any.
    """

    roblox_user: RobloxUser | None = None

    if includes is None:
        includes = ["groups"]

    if roblox_id and roblox_username:
        raise ValueError("You cannot provide both a roblox_id and a roblox_username.")

    if user and (roblox_username or roblox_id):
        raise ValueError(
            "You cannot provide both a user and a roblox_id or roblox_username."
        )

    if user:
        try:
            roblox_user = await get_user_account(user, guild_id)

        except UserNotVerified:
            if raise_on_unverified:
                raise

        if roblox_user:
            await roblox_user.sync(includes)

    else:
        roblox_user = RobloxUser(username=roblox_username, id=roblox_id)
        await roblox_user.sync(includes)

    return roblox_user


async def get_accounts(user_id: int) -> list[RobloxUser]:
    """Get a user's linked Roblox accounts.

    Args:
        user_id (int): The user to get linked Roblox accounts for.

    Returns:
        list[RobloxUser]: The linked Roblox accounts for this user.
    """

    bloxlink_user = await fetch_user_data(user_id, "robloxID", "robloxAccounts")
    account_ids = set()

    if bloxlink_user.robloxID:
        account_ids.add(bloxlink_user.robloxID)

    guild_accounts = (bloxlink_user.robloxAccounts or {}).get("guilds") or {}

    for guild_account_id in guild_accounts.values():
        account_ids.add(guild_account_id)

    accounts = [RobloxUser(id=account_id) for account_id in account_ids]

    return accounts


async def reverse_lookup(
    roblox_user: RobloxUser, exclude_user_id: int | None = None
) -> list[int]:
    """Find Discord IDs linked to a roblox id.

    Args:
        roblox_user (RobloxUser): The roblox account that will be matched against.
        exclude_user_id (int | None, optional): Discord user ID that will not be included in the output.
            Defaults to None.

    Returns:
        list[int]: All the discord IDs linked to this roblox_id.
    """

    roblox_id = str(roblox_user.id)

    cursor = mongo.bloxlink["users"].find(
        {"$or": [{"robloxID": roblox_id}, {"robloxAccounts.accounts": roblox_id}]},
        {"_id": 1},
    )

    return [
        int(x["_id"]) async for x in cursor if str(exclude_user_id) != str(x["_id"])
    ]


async def get_user_from_string(
    target: Annotated[str, "Roblox username or ID"],
) -> RobloxUser:
    """Get a RobloxUser from a given target string (either an ID or username)

    Args:
        target (str): Roblox ID or username of the account to sync.

    Raises:
        RobloxNotFound: When no user is found.
        *Other exceptions may be raised such as RobloxAPIError from get_user*

    Returns:
        RobloxAccount: The synced RobloxAccount of the user requested.
    """

    account = None

    if target.isdigit():
        try:
            account = await get_user(roblox_id=target)
        except (RobloxNotFound, RobloxAPIError):
            pass

    # Fallback to parse input as a username if the input was not a valid id.
    if not account:
        try:
            account = await get_user(roblox_username=target)
        except RobloxNotFound as exc:
            raise RobloxNotFound(
                "The Roblox user you were searching for does not exist! "
                "Please check the input you gave and try again!"
            ) from exc

    if account.id is None or account.username is None:
        raise RobloxNotFound("The Roblox user you were searching for does not exist.")

    return account
