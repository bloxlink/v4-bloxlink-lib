from enum import Enum
from typing import Callable
from datetime import datetime
from unittest.mock import AsyncMock
from bloxlink_lib.models import binds
from bloxlink_lib import (
    RoleSerializable,
    RobloxEntity,
    RobloxGroup,
    GroupRoleset,
    RobloxUserGroup,
    BaseModel,
    MemberSerializable,
    RobloxUser,
    RobloxBaseAsset,
)
from bloxlink_lib.models.base.serializable import GuildSerializable
from bloxlink_lib.models.schemas.guilds import GuildData
from bloxlink_lib.test_utils.utils import generate_snowflake

__all__ = [
    "mock_entity_sync",
    "mock_bind",
    "mock_group",
    "mock_guild_roles",
    "mock_guild",
    "mock_discord_user",
    "mock_roblox_user",
    "mock_user",
    "MockUserData",
    "MockUser",
    "mock_guild_data",
]


def mock_entity_sync(mocker, entity: RobloxEntity) -> None:
    """Mock the sync method for an entity to do nothing"""

    mocked_sync = mocker.AsyncMock(return_value=None)
    mocker.patch.object(entity, "sync", new=mocked_sync)


def mock_bind(
    mocker,
    *,
    discord_roles: list[RoleSerializable],
    criteria: binds.BindCriteria,
    entity: RobloxEntity,
    nickname: str = "{roblox-name}",
) -> binds.GuildBind:
    """Mock a bind"""

    new_bind = binds.GuildBind(
        nickname=nickname,
        roles=[str(role.id) for role in discord_roles],
        criteria=criteria,
    )

    # Mock the sync method to prevent actual API calls
    mocked_sync = mocker.AsyncMock(return_value=None)
    mocker.patch.object(RobloxGroup, "sync", new=mocked_sync)

    new_bind.entity = entity

    return new_bind


def mock_group(mocker, roleset_names: list[str]) -> RobloxGroup:
    """Mock a group"""

    mock_entity_sync(mocker, RobloxGroup)

    group_rolesets = {
        i: GroupRoleset(id=i, name=name, rank=i) for i, name in enumerate(roleset_names)
    }

    return RobloxGroup(
        id=generate_snowflake(),
        name="Military Roleplay Community",
        rolesets=group_rolesets,
    )


def mock_guild_roles(role_names: list[str]) -> dict[int, RoleSerializable]:
    """Mock Discord roles for a Discord server"""

    guild_roles: dict[int, RoleSerializable] = {}

    for i, role_name in enumerate(role_names):
        guild_roles[i] = RoleSerializable(id=i, name=role_name, position=i)

    return guild_roles


def mock_guild(role_names: list[str]):
    """Mock a Discord server"""

    guild_roles = mock_guild_roles(role_names)

    return GuildSerializable(
        id=generate_snowflake(),
        name="Military Roleplay Community",
        roles=guild_roles,
    )


class MockUserData(BaseModel):
    """Data to use for the mocked user"""

    current_group_roleset: Enum | None = None
    current_discord_roles: list[Enum]  # Set the user's current Discord roles
    verified: bool = True
    owns_assets: list[Enum] | None = None


class MockUser(BaseModel):
    """Discord user model with optional linked Roblox account"""

    discord_user: MemberSerializable  # The Discord user
    roblox_user: RobloxUser | None  # The Roblox account of the user. Optional.
    owns_assets: list[Enum] | None = None  # Passed from MockUserData (the test case)


def _mock_user_owns_asset(
    mocked_asset: Enum,
) -> Callable[[RobloxBaseAsset], bool]:
    """Mock the user's owns_asset method to return True when called with this asset (badge, gamepass, catalog asset) ID"""

    def _mock_owns_asset(asset: RobloxBaseAsset) -> bool:
        if mocked_asset.value == asset.id:
            return True

        return False

    return _mock_owns_asset


def mock_roblox_user(
    mocker,
    *,
    user_id: int,
    username: str,
    groups: dict[int, RobloxUserGroup] | None,
    owns_assets: list[Enum] | None,
) -> RobloxUser:
    roblox_user = RobloxUser(
        id=user_id,
        username=username,
        display_name=username.title(),
        created=datetime.fromisoformat("2021-01-01T00:00:00.000000+00:00").replace(
            tzinfo=None
        ),
        groups=groups,
    )

    # Do not sync the model with the Roblox API
    mock_entity_sync(mocker, RobloxUser)

    if owns_assets:
        for mocked_asset in owns_assets:
            mocker.patch.object(
                RobloxUser,
                "owns_asset",
                new=mocker.AsyncMock(side_effect=_mock_user_owns_asset(mocked_asset)),
            )
    else:
        # Skip Roblox API calls
        mocker.patch.object(
            RobloxUser,
            "owns_asset",
            new=mocker.AsyncMock(return_value=False),
        )

    return roblox_user


def mock_discord_user(
    user_id: int,
    username: str,
    guild: GuildSerializable,
    current_discord_roles: list[int],
) -> MemberSerializable:

    discord_user = MemberSerializable(
        id=user_id,
        global_name=username.title(),
        username=username,
        avatar_url="https://cdn.discordapp.com/avatars/123/abc.png",
        is_bot=False,
        joined_at="2021-01-01T00:00:00.000000+00:00",
        role_ids=current_discord_roles,
        guild_id=guild.id,
        nickname=username,
        mention=f"<@{user_id}>",
    )

    return discord_user


def mock_user(
    mocker,
    *,
    verified: bool,
    username: str,
    guild: GuildSerializable,
    groups: dict[int, RobloxUserGroup] | None = None,
    current_discord_roles: list[int] | None = None,
    owns_assets: list[Enum] | None = None,
) -> MockUser:
    """Mock a Roblox and Discord user"""

    user_id = generate_snowflake()
    current_discord_roles = current_discord_roles or []
    groups = groups or {}

    member = mock_discord_user(
        user_id=user_id,
        username=username,
        guild=guild,
        current_discord_roles=current_discord_roles,
    )

    roblox_user = (
        mock_roblox_user(
            mocker,
            user_id=user_id,
            username=username,
            groups=groups,
            owns_assets=owns_assets,
        )
        if verified
        else None
    )

    return MockUser(
        discord_user=member,
        roblox_user=roblox_user,
        owns_assets=owns_assets,
    )


def mock_guild_data(
    mocker,
    guild_data: GuildData,
) -> None:
    """Mock the guild's stored data"""

    # Mock the Redis cache calls to return empty (cache miss)
    mocker.patch(
        "bloxlink_lib.database.redis.redis.hmget",
        new_callable=AsyncMock,
        return_value={},
    )
    mocker.patch(
        "bloxlink_lib.database.redis.redis.hgetall",
        new_callable=AsyncMock,
        return_value={},
    )

    # Mock the raw MongoDB call _db_fetch to return our test data
    async def _mock_db_fetch(constructor, item_id, *aspects):
        data = guild_data.model_dump(by_alias=True, exclude_unset=True)
        data["_id"] = item_id

        return data

    mocker.patch(
        "bloxlink_lib.database.mongodb._db_fetch",
        new_callable=AsyncMock,
        side_effect=_mock_db_fetch,
    )
