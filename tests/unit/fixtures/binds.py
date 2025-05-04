import pytest
from bloxlink_lib.models import binds
from bloxlink_lib import RobloxGroup, GroupBindData

# fixtures
from .guilds import guild_roles
from .groups import test_test_group


# Bind scenarios (user does/does not meet bind condition)
@pytest.fixture(scope="module")
def entire_group_bind(
    module_mocker,
    guild_roles,
    test_test_group: RobloxGroup,
) -> binds.GuildBind:
    """Whole group binds for V3 with 1 group linked."""

    # everyone in the group will receive guild_roles
    new_bind = binds.GuildBind(
        nickname="{roblox-name}",
        roles=[str(role_id) for role_id in guild_roles.keys()],
        criteria=binds.BindCriteria(
            type="group", id=test_test_group.id, group=GroupBindData(everyone=True)
        ),
    )

    # Mock the sync method to prevent actual API calls
    mocked_sync = module_mocker.AsyncMock(return_value=None)
    module_mocker.patch.object(RobloxGroup, "sync", new=mocked_sync)

    return new_bind
