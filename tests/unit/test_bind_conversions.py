import pytest
from bloxlink_lib.models import binds
from tests.unit.fixtures.bind_conversions import BindConversionTestCase


pytestmark = pytest.mark.bind_conversions


class TestBindConversions:
    """Tests for converting V3 binds to V4."""

    def test_bind_length(
        self, bind_conversion_test_data: BindConversionTestCase
    ):  # pylint: disable=W0621
        """Test that the converted binds have the correct length."""

        v3_binds = bind_conversion_test_data.v3_binds
        correct_v4_binds = bind_conversion_test_data.v4_binds

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert len(converted_binds) == len(
            correct_v4_binds
        ), f"Converted binds should have {len(correct_v4_binds)} binds."

    def test_bind_equals_same_bind(
        self, bind_conversion_test_data: BindConversionTestCase
    ):  # pylint: disable=W0621
        """Test that the converted binds equal the same binds."""

        v3_binds = bind_conversion_test_data.v3_binds
        correct_v4_binds = bind_conversion_test_data.v4_binds

        converted_binds = binds.GuildBind.from_V3(v3_binds)

        assert all(
            converted_bind == correct_bind
            for converted_bind, correct_bind in zip(converted_binds, correct_v4_binds)
        )

    def test_bind_equals_another(
        self, bind_conversion_test_data: BindConversionTestCase
    ):  # pylint: disable=W0621
        """Test that the converted binds equal the same binds."""

        print(bind_conversion_test_data.v4_binds)
        print(binds.GuildBind.from_V3(bind_conversion_test_data.v3_binds))

        assert bind_conversion_test_data.v4_binds == binds.GuildBind.from_V3(
            bind_conversion_test_data.v3_binds
        )
