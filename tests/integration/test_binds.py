import pytest
from bloxlink_lib.models.roblox.binds import delete_bind, get_binds
from bloxlink_lib.models.schemas.guilds import (  # pylint: disable=no-name-in-module
    update_guild_data,
)
from tests.shared import BindConversionTestCase

pytestmark = pytest.mark.binds


class TestIntegrationV3BindRemovals:
    """Tests the removal of V3 binds."""

    @pytest.mark.asyncio
    async def test_v3_group_bind_removal_all_binds(
        self, test_guild_id: int, bind_conversion_test_data: BindConversionTestCase
    ):
        """Test the removal of a V3 group bind"""

        v3_binds = bind_conversion_test_data.v3_binds

        await update_guild_data(
            test_guild_id,
            roleBinds=v3_binds.roleBinds.model_dump(exclude_unset=True, by_alias=True),
            groupIDs=v3_binds.groupIDs.model_dump(exclude_unset=True, by_alias=True),
        )

        merged_binds = await get_binds(test_guild_id)

        await delete_bind(test_guild_id, *merged_binds)

        assert len(await get_binds(test_guild_id)) == 0

    @pytest.mark.asyncio
    async def test_v3_group_bind_removal_one_at_a_time(
        self, test_guild_id: int, bind_conversion_test_data: BindConversionTestCase
    ):
        """Test the removal of a V3 group bind"""

        v3_binds = bind_conversion_test_data.v3_binds

        await update_guild_data(
            test_guild_id,
            roleBinds=v3_binds.roleBinds.model_dump(exclude_unset=True, by_alias=True),
            groupIDs=v3_binds.groupIDs.model_dump(exclude_unset=True, by_alias=True),
        )

        merged_binds = await get_binds(test_guild_id)

        for bind in list(merged_binds):
            await delete_bind(test_guild_id, bind)

            assert bind not in await get_binds(test_guild_id)

    @pytest.mark.asyncio
    async def test_v3_group_bind_removal_with_v4_binds(
        self, test_guild_id: int, bind_conversion_test_data: BindConversionTestCase
    ):
        """Test the removal of a V3 group bind"""

        v3_binds = bind_conversion_test_data.v3_binds
        v4_binds = bind_conversion_test_data.v4_binds

        await update_guild_data(
            test_guild_id,
            roleBinds=v3_binds.roleBinds.model_dump(exclude_unset=True, by_alias=True),
            groupIDs=v3_binds.groupIDs.model_dump(exclude_unset=True, by_alias=True),
            binds=v4_binds.model_dump(exclude_unset=True, by_alias=True),
        )

        merged_binds = await get_binds(test_guild_id)

        for bind in list(merged_binds):
            await delete_bind(test_guild_id, bind)

            assert bind not in await get_binds(test_guild_id)

    @pytest.mark.asyncio
    async def test_v4_group_bind_removal(
        self, test_guild_id: int, bind_conversion_test_data: BindConversionTestCase
    ):
        """Test the removal of a V4 group bind"""

        v4_binds = bind_conversion_test_data.v4_binds

        await update_guild_data(
            test_guild_id,
            binds=v4_binds.model_dump(exclude_unset=True, by_alias=True),
        )

        merged_binds = await get_binds(test_guild_id)

        assert len(merged_binds) == len(v4_binds)

        for bind in list(merged_binds):
            await delete_bind(test_guild_id, bind)

            assert bind not in await get_binds(test_guild_id)


class TestBindProperties:
    """Tests the utils for binds."""

    @pytest.mark.asyncio
    async def test_bind_hash_equals(
        self, test_guild_id: int, bind_conversion_test_data: BindConversionTestCase
    ):
        """Test the hash of a bind"""

        binds = bind_conversion_test_data.v4_binds

        await update_guild_data(
            test_guild_id,
            binds=binds.model_dump(exclude_unset=True, by_alias=True),
        )

        merged_binds = await get_binds(test_guild_id)

        assert len(merged_binds) == len(binds)

        for i, bind in enumerate(merged_binds):
            assert hash(bind) == hash(binds[i])

    @pytest.mark.asyncio
    async def test_bind_hash_get_binds_multiple_calls(
        self, test_guild_id: int, bind_conversion_test_data: BindConversionTestCase
    ):
        """Test that get_binds returns the same bind multiple times"""

        binds = bind_conversion_test_data.v4_binds

        await update_guild_data(
            test_guild_id,
            binds=binds.model_dump(exclude_unset=True, by_alias=True),
        )

        merged_binds_1 = await get_binds(test_guild_id)
        merged_binds_2 = await get_binds(test_guild_id)

        assert merged_binds_1 == merged_binds_2

        for bind_1, bind_2 in zip(merged_binds_1, merged_binds_2):
            assert hash(bind_1.criteria) == hash(bind_2.criteria)
            assert hash(bind_1) == hash(bind_2)
            assert hash(bind_1) == hash(bind_2.criteria) and hash(bind_2) == hash(
                bind_1.criteria
            )
