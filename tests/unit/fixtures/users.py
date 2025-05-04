from datetime import datetime
from typing import Annotated
import pytest
from pydantic import Field
from bloxlink_lib import (
    MemberSerializable,
    BaseModel,
    RobloxUser,
    GuildSerializable,
    RobloxUserGroup,
    RobloxGroup,
    GroupRoleset,
    RoleSerializable,
    find,
)
from tests.unit.utils import generate_snowflake, filter_enum_list

# fixtures
from .guilds import test_guild, GuildRoles, guild_roles
from .groups import (
    GroupRolesetsType,
    test_group,
    member_roleset,
    GroupRolesets,
    group_rolesets,
)


class MockUserData(BaseModel):
    """Data to use for the mocked user"""

    current_group_roleset: GroupRolesets
    current_discord_roles: list[GuildRoles]  # Set the user's current Discord roles
    # expected_discord_roles: Annotated[
    #     list[GuildRoles], Field(default_factory=list)
    # ]  # Passed to MockUser to use in the test case. Defaults to empty array.


class MockUser(BaseModel):
    """Discord user model with optional linked Roblox account"""

    discord_user: MemberSerializable  # The Discord user
    roblox_user: RobloxUser | None  # The Roblox account of the user. Optional.
    expected_discord_roles: list[int] = (
        None  # Used by the test case. Injected by mock_user fixture. Optional.
    )


def _mock_roblox_user(
    module_mocker,
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
    mocked_sync = module_mocker.AsyncMock(return_value=None)
    module_mocker.patch.object(RobloxUser, "sync", new=mocked_sync)

    return roblox_user


def _mock_discord_user(
    user_id: int,
    username: str,
    guild: GuildSerializable,
    current_discord_roles: list[GuildRoles],
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


def _mock_user(
    module_mocker,
    username: str,
    guild: GuildSerializable,
    groups: RobloxUserGroup,
    current_discord_roles: list[int] | None = None,
) -> MockUser:
    user_id = generate_snowflake()
    current_discord_roles = current_discord_roles or []

    member = _mock_discord_user(
        user_id=user_id,
        username=username,
        guild=guild,
        current_discord_roles=current_discord_roles,
    )

    roblox_user = _mock_roblox_user(
        module_mocker, user_id=user_id, username=username, groups=groups
    )

    return MockUser(discord_user=member, roblox_user=roblox_user)


@pytest.fixture(scope="module")
def test_group_member(
    module_mocker,
    test_guild: GuildSerializable,
    test_group: RobloxGroup,
    member_roleset: GroupRoleset,
) -> MockUser:
    """Test Discord Member model."""

    user = _mock_user(
        module_mocker,
        username="john",
        guild=test_guild,
        groups={test_group.id: RobloxUserGroup(group=test_group, role=member_roleset)},
    )

    return user


@pytest.fixture(scope="module")
def mock_user(
    module_mocker,
    request,
    test_guild: GuildSerializable,
    test_group: RobloxGroup,
    group_rolesets: GroupRolesetsType,
    guild_roles: dict[int, RoleSerializable],
) -> MockUser:
    """Mock a user for a test case."""

    mock_data: MockUserData = request.param

    current_discord_roles: list[int] = [
        r.id
        for r in guild_roles.values()
        if r.name in filter_enum_list(mock_data.current_discord_roles)
    ]
    # expected_discord_roles: list[int] = [
    #     r.id
    #     for r in guild_roles.values()
    #     if r.name in filter_enum_list(mock_data.expected_discord_roles)
    # ]
    current_group_roleset = find(
        lambda r: r.name in mock_data.current_group_roleset.value,
        group_rolesets.values(),
    )

    if not current_group_roleset:
        raise ValueError("Unable to find matching Roleset from Mocked Group")

    user = _mock_user(
        module_mocker,
        username="john",
        guild=test_guild,
        groups={
            test_group.id: RobloxUserGroup(group=test_group, role=current_group_roleset)
        },
        current_discord_roles=current_discord_roles,
    )

    # user.expected_discord_roles = expected_discord_roles  # For the test case to use

    return user
