import pytest
from bloxlink_lib.models import binds
from bloxlink_lib.models.v3_binds import *


class BindConversionTestCase(BaseModel):
    """A test case for bind conversions. V3 binds must be converted to V4 binds."""

    v3_binds: V3RoleBinds
    v4_binds: list[binds.GuildBind]


@pytest.fixture(
    scope="session",
    params=[
        BindConversionTestCase(
            v3_binds=V3RoleBinds(
                roleBinds={
                    "groups": {
                        "1": V3GroupBind(
                            binds={
                                "1": V3RoleBind(
                                    roles=["566422392533024778", "456584045581565957"],
                                    nickname="sds",
                                    removeRoles=["456584045581565957"],
                                ),
                                "all": V3RoleBind(
                                    roles=["566422392533024778", "456584045581565957"],
                                    nickname="sds",
                                    removeRoles=["456584045581565957"],
                                ),
                            },
                            ranges=[],
                            groupName="RobloHunks",
                            removeRoles=["456584045581565957"],
                        )
                    }
                }
            ),
            v4_binds=[
                binds.GuildBind(
                    criteria=binds.BindCriteria(
                        type="group", id=1, group=binds.GroupBindData(roleset=1)
                    ),
                    nickname="sds",
                    roles=["566422392533024778", "456584045581565957"],
                    remove_roles=["456584045581565957"],
                    data=binds.BindData(displayName="RobloHunks"),
                ),
                binds.GuildBind(
                    criteria=binds.BindCriteria(
                        type="group", id=1, group=binds.GroupBindData(everyone=True)
                    ),
                    nickname="sds",
                    roles=["566422392533024778", "456584045581565957"],
                    remove_roles=["456584045581565957"],
                    data=binds.BindData(displayName="RobloHunks"),
                ),
            ],
        ),
        BindConversionTestCase(
            v3_binds=V3RoleBinds(
                roleBinds={
                    "groups": {
                        "1": V3GroupBind(
                            binds={
                                "all": V3RoleBind(
                                    roles=["566422392533024778", "456584045581565957"],
                                    nickname="sds",
                                    removeRoles=["456584045581565957"],
                                )
                            },
                            ranges=[],
                            groupName="RobloHunks",
                            removeRoles=["456584045581565957"],
                        )
                    }
                }
            ),
            v4_binds=[
                binds.GuildBind(
                    criteria=binds.BindCriteria(
                        type="group", id=1, group=binds.GroupBindData(everyone=True)
                    ),
                    nickname="sds",
                    roles=["566422392533024778", "456584045581565957"],
                    remove_roles=["456584045581565957"],
                    data=binds.BindData(displayName="RobloHunks"),
                )
            ],
        ),
        BindConversionTestCase(
            v3_binds=V3RoleBinds(
                groupIDs={
                    "1": V3GroupID(
                        nickname="{roblox-name}-{group-rank}",
                        groupName="Test Group 1",
                        removeRoles=[],
                    ),
                    "100": V3GroupID(
                        nickname="{roblox-name}",
                        groupName="Test Group 2",
                        removeRoles=["1111111111111111", "2222222222222222"],
                    ),
                }
            ),
            v4_binds=[
                binds.GuildBind(
                    criteria=binds.BindCriteria(
                        type="group", id=1, group=binds.GroupBindData(dynamicRoles=True)
                    ),
                    nickname="{roblox-name}-{group-rank}",
                    remove_roles=[],
                    data=binds.BindData(displayName="Test Group 1"),
                ),
                binds.GuildBind(
                    criteria=binds.BindCriteria(
                        type="group",
                        id=100,
                        group=binds.GroupBindData(dynamicRoles=True),
                    ),
                    nickname="{roblox-name}",
                    remove_roles=["1111111111111111", "2222222222222222"],
                    data=binds.BindData(displayName="Test Group 2"),
                ),
            ],
        ),
        BindConversionTestCase(
            v3_binds=V3RoleBinds(
                roleBinds={
                    "groups": {
                        "1": V3GroupBind(
                            binds={
                                "all": V3RoleBind(
                                    roles=[
                                        "1257118491857653924",
                                        "1258542702547570758",
                                        "456584045581565957",
                                    ],
                                    nickname=None,
                                    removeRoles=["1257857536099618889"],
                                ),
                                "-5": V3RoleBind(
                                    roles=["1258542702547570758", "456584045581565957"],
                                    nickname=None,
                                    removeRoles=["1257857536099618889"],
                                ),
                            },
                            ranges=[
                                V3RangeBinding(
                                    roles=["1258542702547570758", "456584045581565957"],
                                    nickname=None,
                                    removeRoles=["1257857536099618889"],
                                    low=1,
                                    high=5,
                                )
                            ],
                            groupName="RobloHunks",
                            removeRoles=["1257857536099618889"],
                        )
                    },
                    "assets": {
                        "11452821": V3AssetBind(
                            nickname=None,
                            displayName="Claymore",
                            removeRoles=[],
                            roles=["1273731435035103354"],
                        )
                    },
                    "badges": {
                        "2667428956752400": V3BadgeBind(
                            nickname=None,
                            displayName="Spiral Horns of the Developer",
                            removeRoles=[],
                            roles=["1369803939457007779"],
                        )
                    },
                    "gamePasses": {
                        "824168675": V3GamePassBind(
                            nickname="sdaasdsd",
                            displayName="Carry 1 Extra Item ",
                            removeRoles=[],
                            roles=["1369804191232688180"],
                        )
                    },
                }
            ),
            v4_binds=[
                # Group binds
                binds.GuildBind(
                    criteria=binds.BindCriteria(
                        type="group", id=1, group=binds.GroupBindData(everyone=True)
                    ),
                    nickname=None,
                    roles=[
                        "1257118491857653924",
                        "1258542702547570758",
                        "456584045581565957",
                    ],
                    remove_roles=["1257857536099618889"],
                    data=binds.BindData(displayName="RobloHunks"),
                ),
                binds.GuildBind(
                    criteria=binds.BindCriteria(
                        type="group", id=1, group=binds.GroupBindData(roleset=-5)
                    ),
                    nickname=None,
                    roles=["1258542702547570758", "456584045581565957"],
                    remove_roles=["1257857536099618889"],
                    data=binds.BindData(displayName="RobloHunks"),
                ),
                binds.GuildBind(
                    criteria=binds.BindCriteria(
                        type="group",
                        id=1,
                        group=binds.GroupBindData(
                            min=1,
                            max=5,
                        ),
                    ),
                    nickname=None,
                    roles=["1258542702547570758", "456584045581565957"],
                    remove_roles=["1257857536099618889"],
                    data=binds.BindData(displayName="RobloHunks"),
                ),
                # Asset bind
                binds.GuildBind(
                    criteria=binds.BindCriteria(type="asset", id=11452821),
                    nickname=None,
                    roles=["1273731435035103354"],
                    remove_roles=[],
                    data=binds.BindData(displayName="Claymore"),
                ),
                # Badge bind
                binds.GuildBind(
                    criteria=binds.BindCriteria(type="badge", id=2667428956752400),
                    nickname=None,
                    roles=["1369803939457007779"],
                    remove_roles=[],
                    data=binds.BindData(displayName="Spiral Horns of the Developer"),
                ),
                # GamePass bind
                binds.GuildBind(
                    criteria=binds.BindCriteria(type="gamepass", id=824168675),
                    nickname="sdaasdsd",
                    roles=["1369804191232688180"],
                    remove_roles=[],
                    data=binds.BindData(displayName="Carry 1 Extra Item "),
                ),
            ],
        ),
    ],
)
def bind_conversion_test_data(
    request,
) -> BindConversionTestCase:
    return request.param


__all__ = ["bind_conversion_test_data", "BindConversionTestCase"]
