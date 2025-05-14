import pytest
from bloxlink_lib.models import binds
from tests.unit.fixtures.bind_conversions import BindConversionTestCase


pytestmark = pytest.mark.binds


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

    def test_correct_conversion(
        self, bind_conversion_test_data: BindConversionTestCase
    ):  # pylint: disable=W0621
        """Test that binds converted correctly."""

        assert bind_conversion_test_data.v4_binds == binds.GuildBind.from_V3(
            bind_conversion_test_data.v3_binds
        )
