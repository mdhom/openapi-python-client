__all__ = ["EnumProperty"]

from typing import Any, ClassVar, Dict, List, Optional, Set, Type, Union, cast

import attr
import re

from ... import schema as oai
from ... import utils
from .property import Property
from .schemas import Class

ValueType = Union[str, int]

ValidEnumNamesProperties = ["x-enumNames", "x-enumnames", "x-enum-varnames", "x-enumvarnames"]

IsIntegerPattern = re.compile(r"\d*")

def __is_integer(value):
    match = IsIntegerPattern.match(value)
    return match and match.group(0) == value


@attr.s(auto_attribs=True, frozen=True)
class EnumProperty(Property):
    """A property that should use an enum"""

    values: Dict[str, ValueType]
    class_info: Class
    value_type: Type[ValueType]
    default: Optional[Any] = attr.ib()

    template: ClassVar[str] = "enum_property.py.jinja"

    _allowed_locations: ClassVar[Set[oai.ParameterLocation]] = {
        oai.ParameterLocation.QUERY,
        oai.ParameterLocation.PATH,
        oai.ParameterLocation.COOKIE,
        oai.ParameterLocation.HEADER,
    }

    # pylint: disable=unused-argument
    def get_base_type_string(self, *, quoted: bool = False) -> str:
        return self.class_info.name

    def get_base_json_type_string(self, *, quoted: bool = False) -> str:
        return self.value_type.__name__

    def get_imports(self, *, prefix: str) -> Set[str]:
        """
        Get a set of import strings that should be included when this property is used somewhere

        Args:
            prefix: A prefix to put before any relative (local) module names. This should be the number of . to get
            back to the root of the generated client.
        """
        imports = super().get_imports(prefix=prefix)
        imports.add(f"from {prefix}models.{self.class_info.module_name} import {self.class_info.name}")
        return imports

    @staticmethod
    def values_from_list(values: Union[List[str], List[int]], data: oai.Schema) -> Dict[str, ValueType]:
        """Convert a list of values into dict of {name: value}, where value can sometimes be None"""
        output: Dict[str, ValueType] = {}

        names: list[str] = None
        for enum_name in ValidEnumNamesProperties:
            if enum_name in data.__dict__:
                names = data.__dict__[enum_name]
                break

        for i, value in enumerate(values):
            # try cast value to integer for supporting IntEnum generation
            if __is_integer(value):
                value = int(value)

            if names is not None:
                # names are given in x-... property
                key = names[i]
            elif isinstance(value, int):
                # no name given, integer enum
                if value < 0:
                    key = f"VALUE_NEGATIVE_{-value}"
                else:
                    key = f"VALUE_{value}"
            else:
                # no name given, string enum
                if value and value[0].isalpha():
                    key = value.upper()
                else:
                    key = f"VALUE_{i}"
                key = utils.snake_case(key).upper()
                value = utils.remove_string_escapes(value)

            if key in output:
                raise ValueError(f"Duplicate key {key} in Enum")
            output[key] = value
        return output
