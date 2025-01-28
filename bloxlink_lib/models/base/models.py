from pydantic import BaseModel
from typing import Type, Any,  Annotated, Tuple
from pydantic import BaseModel as PydanticBaseModel, BeforeValidator, WithJsonSchema, ConfigDict
from pydantic.fields import FieldInfo
from generics import get_filled_type

Snowflake = Annotated[int, BeforeValidator(
    int), WithJsonSchema({"type": 'int'})]


class UNDEFINED:
    """
    Can be used to differentiate between None and undefined
    in function arguments.
    """


class BaseModelArbitraryTypes(PydanticBaseModel):
    """Base model with arbitrary types allowed."""

    model_config = ConfigDict(arbitrary_types_allowed=True,
                              populate_by_name=True, validate_assignment=True)


class BaseModel(PydanticBaseModel):
    """Base model with a set configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)
    _generic_type_value: Any = None

    @classmethod
    def model_fields_index(cls: Type[PydanticBaseModel | BaseModelArbitraryTypes]) -> list[Tuple[str, FieldInfo]]:
        """Returns a list of the model's fields with the name as a tuple.

        Useful if the field index is necessary.

        """

        fields_with_names: list[Tuple[str, FieldInfo]] = []

        for field_name, field in cls.model_fields.items():
            fields_with_names.append((field_name, field))

        return fields_with_names

    def get_type(self) -> Any:
        if self._generic_type_value:
            return self._generic_type_value

        self._generic_type_value = get_filled_type(self, BaseModel, 0)

        return self._generic_type_value
