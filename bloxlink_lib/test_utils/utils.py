from snowflake import SnowflakeGenerator

from bloxlink_lib.models import binds
from bloxlink_lib import RoleSerializable, RobloxEntity, RobloxGroup

snowflake_generator = SnowflakeGenerator(1)


def generate_snowflake() -> int:
    """Utility to generate Twitter Snowflakes"""

    return next(snowflake_generator)


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
