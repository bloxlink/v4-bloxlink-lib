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


def _mock_bind(
    module_mocker,
    *,
    discord_roles: list[RoleSerializable],
    criteria: binds.BindCriteria,
    nickname: str = "{roblox-name}",
) -> binds.GuildBind:
    """Mock a bind"""

    new_bind = binds.GuildBind(
        nickname=nickname,
        roles=[str(role.id) for role in discord_roles],
        criteria=criteria,
    )

    # Mock the sync method to prevent actual API calls
    mocked_sync = module_mocker.AsyncMock(return_value=None)
    module_mocker.patch.object(RobloxGroup, "sync", new=mocked_sync)

    return new_bind


# Bind scenarios (user does/does not meet bind condition)


# Group bind fixtures
@pytest.fixture(scope="module")
def everyone_group_bind(
    module_mocker,
    find_discord_roles: Callable[[GuildRoles, ...], list[RoleSerializable]],
    test_group: RobloxGroup,
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = _mock_bind(
        module_mocker,
        discord_roles=find_discord_roles(GuildRoles.RANK_1),
        criteria=binds.BindCriteria(
            type="group", id=test_group.id, group=GroupBindData(everyone=True)
        ),
    )

    return mocked_bind


# Verified bind fixtures
@pytest.fixture(scope="module")
def verified_bind(
    module_mocker,
    find_discord_roles: Callable[[GuildRoles, ...], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = _mock_bind(
        module_mocker,
        discord_roles=find_discord_roles(GuildRoles.VERIFIED),
        criteria=binds.BindCriteria(type="verified"),
    )

    return mocked_bind


# Unverified bind fixtures
@pytest.fixture(scope="module")
def unverified_bind(
    module_mocker,
    find_discord_roles: Callable[[GuildRoles, ...], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = _mock_bind(
        module_mocker,
        discord_roles=find_discord_roles(GuildRoles.UNVERIFIED),
        criteria=binds.BindCriteria(type="unverified"),
    )

    return mocked_bind
