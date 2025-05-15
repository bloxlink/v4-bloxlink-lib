from datetime import datetime
from typing import Callable
import pytest
from bloxlink_lib import (
    MemberSerializable,
    BaseModel,
    RobloxUser,
    GuildSerializable,
    RobloxUserGroup,
    RobloxGroup,
    GroupRoleset,
    RobloxBaseAsset,
)
from tests.unit.utils import generate_snowflake
from .groups import GroupRolesets
from .guilds import GuildRoles
from .assets import MockAssets

__all__ = [
    "MockUserData",
    "MockUser",
    "mock_user",
    "test_group_member",
    "test_group_member_bracketed_roleset",
]


class MockUserData(BaseModel):
    """Data to use for the mocked user"""

    current_group_roleset: GroupRolesets | None = None
    current_discord_roles: list[GuildRoles]  # Set the user's current Discord roles
    verified: bool = True
    owns_assets: list[MockAssets] | None = None


class MockUser(BaseModel):
    """Discord user model with optional linked Roblox account"""

    discord_user: MemberSerializable  # The Discord user
    roblox_user: RobloxUser | None  # The Roblox account of the user. Optional.
    owns_assets: list[MockAssets] | None = (
        None  # Passed from MockUserData (the test case)
    )


def _mock_user_owns_asset(
    mocked_asset: MockAssets,
) -> Callable[[RobloxBaseAsset], bool]:
    """Mock the user's owns_asset method to return True when called with this asset (badge, gamepass, catalog asset) ID"""

    def _mock_owns_asset(asset: RobloxBaseAsset) -> bool:
        if mocked_asset.value == asset.id:
            return True

        return False

    return _mock_owns_asset


def _mock_roblox_user(
    mocker,
    *,
    user_id: int,
    username: str,
    groups: dict[int, RobloxUserGroup] | None,
    owns_assets: list[MockAssets] | None,
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
    owns_assets: list[MockAssets] | None = None,
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

    roblox_user = (
        _mock_roblox_user(
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


@pytest.fixture()
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


@pytest.fixture()
def test_group_member_bracketed_roleset(
    mocker,
    test_guild: GuildSerializable,
    test_group: RobloxGroup,
) -> MockUser:
    """Test Discord Member model with a bracketed roleset"""

    user = mock_user(
        mocker,
        verified=True,
        username="john",
        guild=test_guild,
        groups={
            test_group.id: RobloxUserGroup(
                group=test_group,
                role=GroupRoleset(
                    name="[L1] Recruit",
                    rank=1,
                    id=1,
                    memberCount=1,
                ),
            )
        },
    )

    return user
