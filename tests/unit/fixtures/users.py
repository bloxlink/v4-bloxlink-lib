from datetime import datetime
import pytest
from bloxlink_lib import (
    MemberSerializable,
    BaseModel,
    RobloxUser,
    GuildSerializable,
    RobloxUserGroup,
    RobloxGroup,
    GroupRoleset,
)
from tests.unit.utils import generate_snowflake
from . import GroupRolesets, GuildRoles

__all__ = ["MockUserData", "MockUser", "mock_user", "test_group_member"]


class MockUserData(BaseModel):
    """Data to use for the mocked user"""

    current_group_roleset: GroupRolesets | None
    current_discord_roles: list[GuildRoles]  # Set the user's current Discord roles
    verified: bool = True


class MockUser(BaseModel):
    """Discord user model with optional linked Roblox account"""

    discord_user: MemberSerializable  # The Discord user
    roblox_user: RobloxUser | None  # The Roblox account of the user. Optional.


def _mock_roblox_user(
    mocker,
    *,
    user_id: int,
    username: str,
    groups: dict[int, RobloxUserGroup] | None,
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
    mocked_sync = mocker.AsyncMock(return_value=None)
    mocker.patch.object(RobloxUser, "sync", new=mocked_sync)

    return roblox_user


def _mock_discord_user(
    user_id: int,
    username: str,
    guild: GuildSerializable,
    current_discord_roles: list["GuildRoles"],
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
) -> MockUser:
    user_id = generate_snowflake()
    current_discord_roles = current_discord_roles or []
    groups = groups or {}

    member = _mock_discord_user(
        user_id=user_id,
        username=username,
        guild=guild,
        current_discord_roles=current_discord_roles,
    )

    if verified:
        roblox_user = _mock_roblox_user(
            mocker, user_id=user_id, username=username, groups=groups
        )
    else:
        roblox_user = None

    return MockUser(discord_user=member, roblox_user=roblox_user)


@pytest.fixture(scope="function")
def test_group_member(
    mocker,
    test_guild: GuildSerializable,
    test_group: RobloxGroup,
    member_roleset: GroupRoleset,
) -> MockUser:
    """Test Discord Member model."""

    user = mock_user(
        mocker,
        verified=True,
        username="john",
        guild=test_guild,
        groups={test_group.id: RobloxUserGroup(group=test_group, role=member_roleset)},
    )

    return user
