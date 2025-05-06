from bloxlink_lib.models.base.serializable import MemberSerializable, GuildSerializable
from bloxlink_lib import (
    RoleSerializable,
    RobloxGroup,
    RobloxUser,
    RobloxEntity,
)
from bloxlink_lib.models import binds


def nickname_formatter(
    expected_nickname_format: str | None = None,
    roblox_user: RobloxUser | None = None,
    discord_user: MemberSerializable | None = None,
    guild: GuildSerializable | None = None,
) -> str | None:
    """Nickname formatter utility."""

    if not expected_nickname_format:
        return None

    return expected_nickname_format.format(
        roblox_user=roblox_user, discord_user=discord_user, guild=guild
    )


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
