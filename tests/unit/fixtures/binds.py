from typing import TYPE_CHECKING, Callable
import pytest
from bloxlink_lib.models import binds
from bloxlink_lib import RobloxGroup, GroupBindData, find
from bloxlink_lib.models.base.serializable import RoleSerializable
from tests.unit.fixtures.guilds import GuildRoles

if TYPE_CHECKING:
    from .guilds import GuildRolesType


# Bind utility fixtures
@pytest.fixture(scope="module")
def find_discord_roles(guild_roles: "GuildRolesType") -> list[RoleSerializable]:
    """Retrieve the Discord roles from the GuildRoles enum"""

    def _find_discord_roles(*role_enums: GuildRoles) -> list[RoleSerializable]:
        return [
            find(lambda r: r.name == role_enum.value, guild_roles.values())
            for role_enum in role_enums
        ]

    return _find_discord_roles


# Bind scenarios (user does/does not meet bind condition)
@pytest.fixture(scope="module")
def everyone_group_bind(
    module_mocker,
    find_discord_roles: Callable[[GuildRoles, ...], list[RoleSerializable]],
    test_group: RobloxGroup,
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    # everyone in the group will receive guild_roles
    new_bind = binds.GuildBind(
        nickname="{roblox-name}",
        roles=[str(role.id) for role in find_discord_roles(GuildRoles.RANK_1)],
        criteria=binds.BindCriteria(
            type="group", id=test_group.id, group=GroupBindData(everyone=True)
        ),
    )

    # Mock the sync method to prevent actual API calls
    mocked_sync = module_mocker.AsyncMock(return_value=None)
    module_mocker.patch.object(RobloxGroup, "sync", new=mocked_sync)

    return new_bind
