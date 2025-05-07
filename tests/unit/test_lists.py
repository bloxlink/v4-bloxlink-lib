from bloxlink_lib import PydanticList
import pytest

pytestmark = pytest.mark.primitives


class TestPydanticList:
    """Tests related to PydanticList."""

    @pytest.mark.parametrize(
        "input_list, expected_length",
        [
            ([1, 2, 3], 3),
        ],
    )
    def test_pydantic_list_length(self, input_list, expected_length):
        """Test that the PydanticList has the correct length"""

        test_list = PydanticList(root=input_list)

        assert (
            len(test_list) == expected_length
        ), f"PydanticList should have {
            expected_length} items."

    @pytest.mark.parametrize(
        "input_list, value_to_add, expected_length",
        [
            ([1, 2, 3], 4, 4),
        ],
    )
    def test_pydantic_list_add(self, input_list, value_to_add, expected_length):
        """Test that the PydanticList adds an item correctly"""

        test_list = PydanticList(root=input_list)
        test_list.append(value_to_add)

        assert (
            len(test_list) == expected_length
        ), f"PydanticList should have {
            expected_length} items."

    @pytest.mark.parametrize(
        "input_list, expected_str",
        [
            ([1, 2, 3], "[1, 2, 3]"),
        ],
    )
    def test_pydantic_list_str(self, input_list, expected_str):
        """Test that the PydanticList returns a string correctly"""

        test_list = PydanticList(root=input_list)

        assert (
            str(test_list) == expected_str
        ), f"PydanticList should return a string of the items."

    @pytest.mark.parametrize(
        "input_list, value_to_check",
        [
            ([1, 2, 3], 2),
        ],
    )
    def test_pydantic_list_contains(self, input_list, value_to_check):
        """Test that the PydanticList contains a value correctly"""

        test_list = PydanticList(root=input_list)

        assert (
            value_to_check in test_list
        ), f"PydanticList should contain {
            value_to_check}."

    @pytest.mark.parametrize(
        "input_list, value_to_remove, expected_length",
        [
            ([1, 2, 3], 2, 2),
        ],
    )
    def test_pydantic_list_remove(self, input_list, value_to_remove, expected_length):
        """Test that the PydanticList removes a value correctly"""

        test_list = PydanticList(root=input_list)
        test_list.remove(value_to_remove)

        assert (
            len(test_list) == expected_length
        ), f"PydanticList should have {
            expected_length} items."

    @pytest.mark.parametrize(
        "input_list, value_to_pop, expected_length",
        [
            ([1, 2, 3], 1, 2),
        ],
    )
    def test_pydantic_list_pop(self, input_list, value_to_pop, expected_length):
        """Test that the PydanticList pops a value correctly"""

        test_list = PydanticList(root=input_list)
        test_list.pop(value_to_pop)

        assert (
            len(test_list) == expected_length
        ), f"PydanticList should have {
            expected_length} items."

    @pytest.mark.parametrize(
        "input_list, values_to_extend, expected_length",
        [
            ([1, 2, 3], [4, 5], 5),
        ],
    )
    def test_pydantic_list_extend(self, input_list, values_to_extend, expected_length):
        """Test that the PydanticList extends correctly"""

        test_list = PydanticList(root=input_list)
        test_list.extend(values_to_extend)

        assert (
            len(test_list) == expected_length
        ), f"PydanticList should have {
            expected_length} items."

    @pytest.mark.parametrize(
        "input_list, expected_list",
        [
            ([1, 2, 3], [1, 2, 3]),
        ],
    )
    def test_pydantic_list_iter(self, input_list, expected_list):
        """Test that the PydanticList iterates correctly"""

        test_list = PydanticList(root=input_list)

        assert (
            list(test_list) == expected_list
        ), "PydanticList should iterate correctly."

    def test_pydantic_list_empty_list(self):
        """Test that the PydanticList is empty"""

        test_list = PydanticList()

        assert len(test_list) == 0, "PydanticList should be empty."
