from typing import Any, Dict, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from jce.types import JceType
    from jce.field import JceModelField


class JceEncoder:

    @staticmethod
    def encode_byte(jce_id: int, jce_type: Type["JceType"],
                    jce_value: Any) -> bytes:
        return jce_type.to_bytes(jce_id, jce_value)

    @classmethod
    def encode(cls, fields: Dict[str, "JceModelField"],
               data: Dict[str, Any]) -> bytes:
        byte = bytes()
        for name, field in fields.items():
            jce_id = field.jce_id
            jce_type = field.jce_type
            jce_value = data[name]
            byte += cls.encode_byte(jce_id, jce_type, jce_value)
        return byte
