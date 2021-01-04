from typing import Any, Dict, Type

from jce.field import JceType, JceModelField


class JceEncoder:

    @staticmethod
    def encode_byte(jce_id: int, jce_type: Type[JceType], jce_value: Any):
        # TODO: jce_id
        return jce_type.to_byte(jce_value)

    @classmethod
    def encode(cls, fields: Dict[str, JceModelField], data: Dict[str, Any]):
        # TODO: concat
        for name, field in fields.items():
            jce_id = field.jce_id
            jce_type = field.jce_type
            jce_value = data[name]
            cls.encode_byte(jce_id, jce_type, jce_value)
