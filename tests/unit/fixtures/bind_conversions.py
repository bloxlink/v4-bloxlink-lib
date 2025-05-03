import pytest
from bloxlink_lib.models import binds

from .data.binds import *


# Bind conversions (V3 -> V4)
@pytest.fixture()
def v3_rolebinds_1() -> tuple[dict[str, dict[str, dict]], list[binds.GuildBind]]:
    return V3_ROLEBIND_1, V4_ROLEBIND_1


@pytest.fixture()
def v3_rolebinds_2() -> tuple[dict[str, dict[str, dict]], list[binds.GuildBind]]:
    return V3_ROLEBIND_2, V4_ROLEBIND_2


@pytest.fixture()
def v3_group_conversion_1() -> tuple[dict[str, dict[str, dict]], list[binds.GuildBind]]:
    """Whole group binds for V3 with 2 groups linked."""

    return V3_WHOLE_GROUP_BIND_1, V4_WHOLE_GROUP_BIND_1


@pytest.fixture()
def v3_group_conversion_2() -> tuple[dict[str, dict[str, dict]], list[binds.GuildBind]]:
    """Whole group binds for V3 with 1 group linked."""

    return V3_WHOLE_GROUP_BIND_2, V4_WHOLE_GROUP_BIND_2
