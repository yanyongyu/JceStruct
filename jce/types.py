import abc
import struct
from typing import Any, List, Dict, Type, Tuple, TypeVar, Mapping, Iterable, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field
from pydantic.main import ModelMetaclass
from pydantic.typing import NoArgAnyCallable
from pydantic.fields import Undefined, ModelField

T = TypeVar("T", bound="JceType")
S = TypeVar("S", bound="JceStruct")


def JceField(
    default: Any = Undefined,
    *,
    jce_id: int,
    jce_type: Optional[Type["JceType"]] = None,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: str = None,
    title: str = None,
    description: str = None,
    const: bool = None,
    gt: float = None,
    ge: float = None,
    lt: float = None,
    le: float = None,
    multiple_of: float = None,
    min_items: int = None,
    max_items: int = None,
    min_length: int = None,
    max_length: int = None,
    regex: str = None,
    **extra: Any,
) -> Any:
    if jce_id < 1:
        raise ValueError(f"Invalid JCE ID: {jce_id}")
    if jce_type and not issubclass(jce_type, JceType):
        raise TypeError(f"Invalid JCE type: {jce_type}")
    return Field(default=default,
                 default_factory=default_factory,
                 alias=alias,
                 title=title,
                 description=description,
                 const=const,
                 gt=gt,
                 ge=ge,
                 lt=lt,
                 le=le,
                 multiple_of=multiple_of,
                 min_items=min_items,
                 max_items=max_items,
                 min_length=min_length,
                 max_length=max_length,
                 regex=regex,
                 jce_id=jce_id,
                 jce_type=jce_type,
                 **extra)


class JceModelField:

    def __init__(self, jce_id: int, jce_type: Type["JceType"]):
        if not isinstance(jce_id, int) or jce_id < 1:
            raise ValueError(f"Invalid JCE ID")
        if not issubclass(jce_type, JceType):
            raise ValueError(f"Invalid JCE Type")
        self.jce_id: int = jce_id
        self.jce_type: Type[JceType] = jce_type

    @classmethod
    def from_modelfield(cls, field: ModelField) -> "JceModelField":
        field_info = field.field_info
        jce_id = field_info.extra.get("jce_id")
        jce_type = field_info.extra.get("jce_type") or field.type_
        return cls(jce_id, jce_type)


def prepare_fields(fields: Dict[str, ModelField]) -> Dict[str, JceModelField]:
    jce_fields: Dict[str, JceModelField] = {}
    for name, field in fields.items():
        try:
            jce_fields[name] = JceModelField.from_modelfield(field)
        except ValueError:
            continue
    return dict(sorted(jce_fields.items(), key=lambda item: item[1].jce_id))


class JceEncoder:

    @staticmethod
    def encode_by_value(jce_id: int, jce_value: "JceType") -> bytes:
        return jce_value.to_bytes(jce_id, jce_value)

    @staticmethod
    def encode_by_type(jce_id: int, jce_type: Type["JceType"],
                       jce_value: Any) -> bytes:
        return jce_type.to_bytes(jce_id, jce_value)

    @classmethod
    def encode_raw(cls, data: Dict[int, "JceType"]) -> bytes:
        byte = bytes()
        for jce_id, jce_value in data.items():
            byte += cls.encode_by_value(jce_id, jce_value)
        return byte

    @classmethod
    def encode(cls, fields: Dict[str, JceModelField], data: Dict[str,
                                                                 Any]) -> bytes:
        byte = bytes()
        for name, field in fields.items():
            jce_id = field.jce_id
            jce_value = data[name]
            if isinstance(jce_value, JceType):
                byte += cls.encode_by_value(jce_id, jce_value)
            else:
                jce_type = field.jce_type
                byte += cls.encode_by_type(jce_id, jce_type, jce_value)
        return byte


class JceDecoder:

    @staticmethod
    def decode_head(jce_byte: bytes) -> Tuple[int, int, int]:
        type_byte: int = struct.unpack_from(">B", jce_byte)[0]
        type_ = type_byte & 0xF
        jce_id = type_byte >> 4
        if jce_id == 0xF:
            jce_id = struct.unpack_from(">B", jce_byte, 1)[0]
            return jce_id, type_, 2
        return jce_id, type_, 1

    @classmethod
    def decode_single(
        cls,
        jce_byte: bytes,
        default_types: Optional[Dict[int, "JceType"]] = None
    ) -> Tuple[int, Any, int]:
        jce_id, type_, head_length = cls.decode_head(jce_byte)
        default_types = default_types or JceStruct.__jce_default_type__
        JceType = default_types.get(type_)
        if not JceType:
            raise ValueError(f"Unknown JceType for id {type_}")
        data, data_length = JceType.from_bytes(jce_byte[head_length:])
        return jce_id, data, head_length + data_length

    @classmethod
    def decode_bytes(
            cls,
            jce_byte: bytes,
            default_types: Optional[Dict[int,
                                         "JceType"]] = None) -> Dict[int, Any]:
        offset = 0
        result = {}
        default_types = default_types or JceStruct.__jce_default_type__
        while offset < len(jce_byte):
            jce_id, data, data_length = cls.decode_single(
                jce_byte[offset:], default_types)
            result[jce_id] = data
            offset += data_length
        return result

    @classmethod
    def decode(cls, jce_struct: Type[S], fields: Dict[str, "JceModelField"],
               data: bytes, **extra) -> S:
        result = {}
        default_type = jce_struct.__jce_default_type__
        jce_data = cls.decode_bytes(data, default_type)
        for name, field in fields.items():
            result[name] = jce_data.get(field.jce_id)
        result.update(extra)
        return jce_struct.parse_obj(result)  # type: ignore


class JceType(abc.ABC):
    __jce_encoder__: Type[JceEncoder] = JceEncoder
    __jce_decoder__: Type[JceDecoder] = JceDecoder

    @classmethod
    def head_byte(cls: Type[T], jce_id: int, jce_type: int) -> bytes:
        if jce_id < 15:
            return bytes([jce_id << 4 | jce_type])
        else:
            return bytes([0xF0 | jce_type, jce_id])

    @classmethod
    @abc.abstractmethod
    def to_bytes(cls: Type[T], jce_id: int, value: Any) -> bytes:
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def from_bytes(cls: Type[T], data: bytes) -> Tuple[Any, int]:
        raise NotImplementedError

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return cls(v)  # type: ignore


class BYTE(JceType, bytes):
    __jce_type__ = (0,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: bytes) -> bytes:
        if len(value) != 1:
            raise ValueError(f"Invalid byte value: {value!r}")
        if value == b"\x00":
            return ZERO_TAG.to_bytes(jce_id, None)
        return cls.head_byte(jce_id, cls.__jce_type__[0]) + value

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[bytes, int]:
        return struct.unpack_from(">c", data)[0], 1

    @classmethod
    def validate(cls, v):
        v = cls(v)
        if len(v) != 1:
            raise ValueError(f"Invalid byte length: {len(v)}")
        return v


class BOOL(JceType, int):
    __jce_type__ = (0,)

    def __new__(cls, value=None):
        return bool(value)

    @classmethod
    def to_byte(cls, jce_id: int, value: bool) -> bytes:
        return cls.head_byte(jce_id, cls.__jce_type__[0]) + struct.pack(
            ">?", value)

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[bool, int]:
        return struct.unpack_from(">?", data)[0], 1

    @classmethod
    def validate(cls, v):
        if isinstance(v, bytes):
            if len(v) != 1:
                raise ValueError(f"Invalid byte length: {len(v)}")
            v, _ = cls.from_bytes(v)
        elif not isinstance(v, bool):
            raise TypeError(f"Invalid value type: {type(v)}")
        return cls(v)


class INT(JceType, int):
    __jce_type__ = (1, 2, 3)

    @classmethod
    def to_bytes(cls, jce_id: int, value: int) -> bytes:
        if -128 <= value <= 127:
            return BYTE.to_bytes(jce_id, struct.pack(">b", value))
        elif -32768 <= value <= 32767:
            return cls.head_byte(jce_id, cls.__jce_type__[0]) + struct.pack(
                ">h", value)
        elif -2147483648 <= value <= 2147483647:
            return cls.head_byte(jce_id, cls.__jce_type__[1]) + struct.pack(
                ">i", value)
        return cls.head_byte(jce_id, cls.__jce_type__[2]) + struct.pack(
            ">q", value)

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[int, int]:
        raise NotImplementedError

    @classmethod
    def validate(cls, v):
        if isinstance(v, bytes):
            v, _ = cls.from_bytes(v)
        elif not isinstance(v, int):
            raise TypeError(f"Invalid value type: {type(v)}")
        return cls(v)


class INT16(INT):

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[int, int]:
        return struct.unpack_from(">h", data)[0], 2


class INT32(INT):

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[int, int]:
        return struct.unpack_from(">i", data)[0], 4


class INT64(INT):

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[int, int]:
        return struct.unpack_from(">q", data)[0], 8


class FLOAT(JceType, float):
    __jce_type__ = (4,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: float) -> bytes:
        return cls.head_byte(jce_id, cls.__jce_type__[0]) + struct.pack(
            ">f", value)

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[float, int]:
        return struct.unpack_from(">f", data)[0], 4

    @classmethod
    def validate(cls, v):
        if isinstance(v, bytes):
            v, _ = cls.from_bytes(v)
        elif not isinstance(v, float):
            raise TypeError(f"Invalid value type: {type(v)}")
        return cls(v)


class DOUBLE(JceType, float):
    __jce_type__ = (5,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: float) -> bytes:
        return cls.head_byte(jce_id, cls.__jce_type__[0]) + struct.pack(
            ">d", value)

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[float, int]:
        return struct.unpack_from(">d", data)[0], 8

    @classmethod
    def validate(cls, v):
        if isinstance(v, bytes):
            v, _ = cls.from_bytes(v)
        elif not isinstance(v, float):
            raise TypeError(f"Invalid value type: {type(v)}")
        return cls(v)


class STRING(JceType, str):
    __jce_type__ = (6, 7)

    @classmethod
    def to_bytes(cls, jce_id: int, value: str) -> bytes:
        byte = value.encode()
        if len(byte) < 256:
            return cls.head_byte(jce_id, cls.__jce_type__[0]) + struct.pack(
                ">B", len(byte)) + byte
        return cls.head_byte(jce_id, cls.__jce_type__[1]) + struct.pack(
            ">I", len(byte)) + byte

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[str, int]:
        raise NotImplementedError

    @classmethod
    def validate(cls, v):
        if isinstance(v, bytes):
            v = v.decode()
        elif not isinstance(v, str):
            raise TypeError(f"Invalid value type: {type(v)}")
        return cls(v)


class STRING1(STRING):

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[str, int]:
        length = struct.unpack_from(">B", data)[0]
        return data[1:length + 1].decode(), length + 1


class STRING4(STRING):

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[str, int]:
        length = struct.unpack_from(">I", data)[0]
        return data[4:length + 4].decode(), length + 4


class MAP(JceType, dict):
    __jce_type__ = (8,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: Dict[JceType, JceType]) -> bytes:
        byte = cls.head_byte(jce_id, cls.__jce_type__[0]) + INT.to_bytes(
            0, len(value))
        for k, v in value.items():
            byte += k.to_bytes(0, k) + v.to_bytes(1, v)
        return byte

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[dict, int]:
        _, data_count, head_length = cls.__jce_decoder__.decode_single(data)

        result = {}
        data_length = head_length
        for _ in range(data_count):
            _, key, key_length = cls.__jce_decoder__.decode_single(
                data[data_length:])
            _, value, value_length = cls.__jce_decoder__.decode_single(
                data[data_length + key_length:])

            result[key] = value
            data_length += key_length + value_length
        return result, data_length

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        if isinstance(v, bytes):
            v, _ = cls.from_bytes(v)
        elif not isinstance(v, Mapping):
            raise TypeError(f"Invalid MAP type: {type(v)}")

        new_instance = cls()
        for key, value in v.items():
            if not isinstance(key, JceType):
                try:
                    key_type = guess_jce_type(key)
                except TypeError:
                    raise TypeError(
                        f"Invalid MAP key: {key}({type(key)})") from None
                key = key_type(key)  # type: ignore
            if not isinstance(value, JceType):
                try:
                    value_type = guess_jce_type(value)
                except TypeError:
                    raise TypeError(
                        f"Invalid MAP value: {value}({type(value)})") from None
                value = value_type(value)  # type: ignore

            new_instance[key] = value

        return new_instance


class LIST(JceType, list):
    __jce_type__ = (9,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: List[JceType]) -> bytes:
        byte = cls.head_byte(jce_id, cls.__jce_type__[0]) + INT.to_bytes(
            0, len(value))
        for v in value:
            byte += v.to_bytes(0, v)
        return byte

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[list, int]:
        _, list_count, head_length = cls.__jce_decoder__.decode_single(data)

        result = []
        data_length = head_length
        for _ in range(list_count):
            _, item, item_length = cls.__jce_decoder__.decode_single(
                data[data_length:])
            result.append(item)
            data_length += item_length
        return result, data_length

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v

        if isinstance(v, bytes):
            v, _ = cls.from_bytes(v)
        elif not isinstance(v, Iterable):
            raise TypeError(f"Invalid LIST type: {type(v)}")

        new_instance = cls()
        for item in v:
            if not isinstance(item, JceType):
                try:
                    item_type = guess_jce_type(item)
                except TypeError:
                    raise TypeError(
                        f"Invalid LIST item type: {type(item)}") from None
                item = item_type(item)  # type: ignore
            new_instance.append(item)
        return new_instance


class STRUCT_START(JceType):
    __jce_type__ = (10,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: Any = None) -> bytes:
        return cls.head_byte(jce_id, cls.__jce_type__[0])

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[Dict[int, Any], int]:
        return JceStruct.from_bytes(data)


class STRUCT_END(JceType):
    __jce_type__ = (11,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: Any = None) -> bytes:
        return cls.head_byte(jce_id, cls.__jce_type__[0])

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[None, int]:
        return None, 0


class ZERO_TAG(JceType):
    __jce_type__ = (12,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: Any = None) -> bytes:
        return cls.head_byte(jce_id, cls.__jce_type__[0])

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[bytes, int]:
        return bytes([0]), 0


class JceMetaclass(ModelMetaclass):

    def __new__(mcs, name, bases, namespace):
        config = namespace.get("Config", object())
        Encoder = getattr(config, "jce_encoder", JceEncoder)
        Decoder = getattr(config, "jce_decoder", JceDecoder)
        default_type = getattr(
            config, "jce_default_type", {
                0: BYTE,
                1: INT16,
                2: INT32,
                3: INT64,
                4: FLOAT,
                5: DOUBLE,
                6: STRING1,
                7: STRING4,
                8: MAP,
                9: LIST,
                10: STRUCT_START,
                11: STRUCT_END,
                12: ZERO_TAG
            })
        if Encoder is not JceEncoder and not issubclass(Encoder, JceEncoder):
            raise TypeError(f"Encoder {Encoder} is not a valid encoder")
        if Decoder is not JceDecoder and not issubclass(Decoder, JceDecoder):
            raise TypeError(f"Decoder {Decoder} is not a valid decoder")
        if any(not issubclass(x, JceType) for x in default_type.values()):
            raise TypeError(f"Invalid default jce type in struct \"{name}\"")
        namespace.update({
            "__jce_encoder__": Encoder,
            "__jce_decoder__": Decoder,
            "__jce_default_type__": default_type
        })
        cls = super().__new__(mcs, name, bases, namespace)  # type: ignore
        fields = prepare_fields(cls.__fields__)
        setattr(cls, "__jce_fields__", fields)
        return cls


class JceStruct(JceType, BaseModel, metaclass=JceMetaclass):

    if TYPE_CHECKING:
        __jce_encoder__: Type["JceEncoder"]
        __jce_decoder__: Type["JceDecoder"]
        __jce_fields__: Dict[str, JceModelField]
        __jce_default_type__: Dict[int, JceType]

    def encode(self):
        return self.__jce_encoder__.encode(self.__jce_fields__, self.dict())

    @classmethod
    def to_bytes(cls, jce_id: int, value) -> bytes:
        return (STRUCT_START.to_bytes(jce_id, None) +
                cls.__jce_encoder__.encode(cls.__jce_fields__, value) +
                STRUCT_END.to_bytes(jce_id, None))

    @classmethod
    def decode(cls, data: bytes, **extra):
        return cls.__jce_decoder__.decode(cls, cls.__jce_fields__, data,
                                          **extra)

    @classmethod
    def from_bytes(cls, data: bytes) -> Tuple[Dict[int, Any], int]:
        offset = 0
        result = {}
        struct_end = False
        while not struct_end and offset < len(data):
            jce_id, data, data_length = cls.__jce_decoder__.decode_single(
                data[offset:])
            offset += data_length
            if data == None:
                struct_end = True
                break
            result[jce_id] = data

        if not struct_end:
            raise ValueError(f"Struct end not found")
        return result, offset


def get_jce_type(jce_id: int) -> JceType:
    return JceStruct.__jce_default_type__[jce_id]


def guess_jce_type(object: Any) -> JceType:
    types = {
        bytes: BYTE,
        bool: BOOL,
        int: INT,
        float: FLOAT,
        str: STRING,
        dict: MAP,
        list: LIST
    }
    for type in types:
        if isinstance(object, type):
            return types[type]
    raise TypeError("Unknown object type")
