from bloxlink_lib.models import binds
from bloxlink_lib import RoleSerializable, RobloxEntity, RobloxGroup, GroupRoleset
from bloxlink_lib.models.base.serializable import GuildSerializable
from bloxlink_lib.test_utils.utils import generate_snowflake

__all__ = [
    "mock_entity_sync",
    "mock_bind",
    "mock_group",
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
        i: GroupRoleset(id=generate_snowflake(), name=name, rank=i)
        for i, name in enumerate(roleset_names)
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
        new_snowflake = generate_snowflake()
        guild_roles[new_snowflake] = RoleSerializable(
            id=new_snowflake, name=role_name, position=i
        )

    return guild_roles


def mock_guild(role_names: list[str]):
    """Mock a Discord server"""

    guild_roles = mock_guild_roles(role_names)

    return GuildSerializable(
        id=generate_snowflake(),
        name="Military Roleplay Community",
        roles=guild_roles,
    )
