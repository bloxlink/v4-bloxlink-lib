from bloxlink_lib import PydanticDict
import pytest

pytestmark = pytest.mark.iterable


class TestPydanticDict:
    """Tests related to PydanticDict."""

    @pytest.mark.parametrize(
        "input_dict, expected_length",
        [
            ({"a": 1, "b": 2, "c": 3}, 3),
        ],
    )
    def test_pydantic_dict_length(self, input_dict, expected_length):
        """Test that the PydanticDict has the correct length"""

        test_dict = PydanticDict(input_dict)

        assert (
            len(test_dict) == expected_length
        ), f"PydanticDict should have {
            expected_length} items."

    @pytest.mark.parametrize(
        "input_dict, key_to_add, value_to_add, expected_length",
        [
            ({"a": 1, "b": 2, "c": 3}, "d", 4, 4),
        ],
    )
    def test_pydantic_dict_add(
        self, input_dict, key_to_add, value_to_add, expected_length
    ):
        """Test that the PydanticDict adds an item correctly"""

        test_dict = PydanticDict(input_dict)
        test_dict[key_to_add] = value_to_add

        assert (
            len(test_dict) == expected_length
        ), f"PydanticDict should have {
            expected_length} items."

    @pytest.mark.parametrize(
        "input_dict, expected_str",
        [
            ({"a": 1, "b": 2, "c": 3}, "{'a': 1, 'b': 2, 'c': 3}"),
        ],
    )
    def test_pydantic_dict_str(self, input_dict, expected_str):
        """Test that the PydanticDict returns a string correctly"""

        test_dict = PydanticDict(input_dict)

        assert (
            str(test_dict) == expected_str
        ), f"PydanticDict should return a string of the items."

    @pytest.mark.parametrize(
        "input_dict, key_to_check",
        [
            ({"a": 1, "b": 2, "c": 3}, "b"),
        ],
    )
    def test_pydantic_dict_contains(self, input_dict, key_to_check):
        """Test that the PydanticDict contains a key correctly"""

        test_dict = PydanticDict(input_dict)

        assert (
            key_to_check in test_dict
        ), f"PydanticDict should contain {
            key_to_check}."

    @pytest.mark.parametrize(
        "input_dict, key_to_remove, expected_length",
        [
            ({"a": 1, "b": 2, "c": 3}, "b", 2),
        ],
    )
    def test_pydantic_dict_remove(self, input_dict, key_to_remove, expected_length):
        """Test that the PydanticDict removes a key correctly"""

        test_dict = PydanticDict(input_dict)

        del test_dict[key_to_remove]

        assert (
            len(test_dict) == expected_length
        ), f"PydanticDict should have {
            expected_length} items."

    @pytest.mark.parametrize(
        "input_dict, key_to_discard, expected_length",
        [
            ({"a": 1, "b": 2, "c": 3}, "b", 2),
        ],
    )
    def test_pydantic_dict_discard(self, input_dict, key_to_discard, expected_length):
        """Test that the PydanticDict discards a key correctly"""

        test_dict = PydanticDict(input_dict)
        test_dict.pop(key_to_discard, None)

        assert (
            len(test_dict) == expected_length
        ), f"PydanticDict should have {
            expected_length} items."

    @pytest.mark.parametrize(
        "input_dict, items_to_update, expected_length",
        [
            ({"a": 1, "b": 2, "c": 3}, {"d": 4, "e": 5}, 5),
        ],
    )
    def test_pydantic_dict_update(self, input_dict, items_to_update, expected_length):
        """Test that the PydanticDict updates correctly"""

        test_dict = PydanticDict(input_dict)
        test_dict.update(items_to_update)

        assert (
            len(test_dict) == expected_length
        ), f"PydanticDict should have {
            expected_length} items."

    @pytest.mark.parametrize(
        "input_dict, expected_list",
        [
            ({"a": 1, "b": 2, "c": 3}, [("a", 1), ("b", 2), ("c", 3)]),
        ],
    )
    def test_pydantic_dict_iter(self, input_dict, expected_list):
        """Test that the PydanticDict iterates correctly"""

        test_dict = PydanticDict(input_dict)

        assert (
            list(test_dict.items()) == expected_list
        ), "PydanticDict should iterate correctly."

    def test_pydantic_dict_empty_dict(self):
        """Test that the PydanticDict is empty"""

        test_dict = PydanticDict()

        assert len(test_dict) == 0, "PydanticDict should be empty."
