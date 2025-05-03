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

# fixtures
from .guilds import military_guild
from .groups import GroupRolesets, test_military_group, member_roleset


class MockUser(BaseModel):
    """Discord user model with optional linked Roblox account"""

    discord_user: MemberSerializable  # The Discord user
    roblox_user: RobloxUser | None  # The Roblox account of the user. Optional.


def _mock_roblox_user(
    mocker, *, user_id: int, username: str, groups: dict[int, RobloxUserGroup] | None
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
    user_id: int, username: str, guild: GuildSerializable
) -> MemberSerializable:
    discord_user = MemberSerializable(
        id=user_id,
        global_name=username.title(),
        username=username,
        avatar_url="https://cdn.discordapp.com/avatars/123/abc.png",
        is_bot=False,
        joined_at="2021-01-01T00:00:00.000000+00:00",
        role_ids=[],
        guild_id=guild.id,
        nickname=username,
        mention=f"<@{user_id}>",
    )

    return discord_user


def _mock_user(
    mocker, username: str, guild: GuildSerializable, groups: RobloxUserGroup
) -> MockUser:
    user_id = generate_snowflake()

    member = _mock_discord_user(user_id=user_id, username=username, guild=guild)

    roblox_user = _mock_roblox_user(
        mocker, user_id=user_id, username=username, groups=groups
    )

    return MockUser(discord_user=member, roblox_user=roblox_user)


@pytest.fixture()
def test_military_member(
    mocker,
    military_guild: GuildSerializable,
    test_military_group: RobloxGroup,
    member_roleset: GroupRoleset,
) -> MockUser:
    """Test Discord Member model."""

    user = _mock_user(
        mocker,
        username="john",
        guild=military_guild,
        groups={
            test_military_group.id: RobloxUserGroup(
                group=test_military_group, role=member_roleset
            )
        },
    )

    return user
