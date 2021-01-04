from typing import Any, Dict, Type, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from jce.types import JceStruct
    from jce.field import JceModelField

T = TypeVar("T", bound="JceStruct")


class JceDecoder:

    @staticmethod
    def decode_byte(data) -> Dict[int, Any]:
        return {}

    @classmethod
    def decode(cls, struct: Type[T], fields: Dict[str, "JceModelField"], data,
               **extra) -> T:
        result = {}
        data = cls.decode_byte(data)
        for name, field in fields.items():
            result[name] = data[field.jce_id]
        result.update(extra)
        return struct.parse_obj(result)  # type: ignore