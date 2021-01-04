import abc
import struct
from typing import Any, List, Dict, Type, TypeVar, Mapping, Iterable, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field
from pydantic.main import ModelMetaclass
from pydantic.typing import NoArgAnyCallable
from pydantic.fields import Undefined, ModelField

from jce.encoder import JceEncoder
from jce.decoder import JceDecoder
from jce.config import BaseConfig, prepare_config

T = TypeVar("T", bound="JceType")


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
    return jce_fields


class JceType(abc.ABC):

    @classmethod
    @abc.abstractmethod
    def to_bytes(cls: Type[T], jce_id: int, value: Any) -> bytes:
        raise NotImplementedError

    # @abc.abstractmethod
    # @classmethod
    # def from_bytes(cls: Type[T], data: bytes) -> T:
    #     raise NotImplementedError


class BYTE(JceType, bytes):
    __jce_type__ = (0,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: bytes) -> bytes:
        if len(value) != 1:
            raise ValueError(f"Invalid byte value: {value!r}")
        return bytes([jce_id << 4 | cls.__jce_type__[0]]) + value


class BOOL(JceType, int):
    __jce_type__ = (0,)

    @classmethod
    def to_byte(cls, jce_id: int, value: bool) -> bytes:
        return bytes([jce_id << 4 | cls.__jce_type__[0]]) + struct.pack(
            ">?", value)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        return cls(bool(v))


class INT(JceType, int):
    __jce_type__ = (1, 2, 3)

    @classmethod
    def to_bytes(cls, jce_id: int, value: int) -> bytes:
        if -128 <= value <= 127:
            return BYTE.to_bytes(jce_id, struct.pack(">b", value))
        elif -32768 <= value <= 32767:
            return bytes([jce_id << 4 | cls.__jce_type__[0]]) + struct.pack(
                ">h", value)
        elif -2147483648 <= value <= 2147483647:
            return bytes([jce_id << 4 | cls.__jce_type__[1]]) + struct.pack(
                ">i", value)
        return bytes([jce_id << 4 | cls.__jce_type__[2]]) + struct.pack(
            ">q", value)


class FLOAT(JceType, float):
    __jce_type__ = (4,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: float) -> bytes:
        return bytes([jce_id << 4 | cls.__jce_type__[0]]) + struct.pack(
            ">f", value)


class DOUBLE(JceType, float):
    __jce_type__ = (5,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: float) -> bytes:
        return bytes([jce_id << 4 | cls.__jce_type__[0]]) + struct.pack(
            ">d", value)


class STRING(JceType, str):
    __jce_type__ = (6, 7)

    @classmethod
    def to_bytes(cls, jce_id: int, value: str) -> bytes:
        byte = value.encode()
        if len(byte) < 256:
            return bytes([jce_id << 4 | cls.__jce_type__[0]]) + struct.pack(
                ">B", len(byte)) + byte
        return bytes([jce_id << 4 | cls.__jce_type__[1]]) + struct.pack(
            ">I", len(byte)) + byte


class MAP(JceType, dict):
    __jce_type__ = (8,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: Dict[JceType, JceType]) -> bytes:
        byte = bytes([jce_id << 4 | cls.__jce_type__[0]]) + INT.to_bytes(
            0, len(value))
        for k, v in value.items():
            byte += k.to_bytes(0, k) + v.to_bytes(1, v)
        return byte

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v
        if v is None:
            return cls()
        if not isinstance(v, Mapping):
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
        byte = bytes([jce_id << 4 | cls.__jce_type__[0]]) + INT.to_bytes(
            0, len(value))
        for v in value:
            byte += v.to_bytes(0, v)
        return byte

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, cls):
            return v
        if not isinstance(v, Iterable):
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
        return bytes([jce_id << 4 | cls.__jce_type__[0]])


class STRUCT_END(JceType):
    __jce_type__ = (11,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: Any = None) -> bytes:
        return bytes([jce_id << 4 | cls.__jce_type__[0]])


class ZERO_TAG(JceType):
    __jce_type__ = (12,)

    @classmethod
    def to_bytes(cls, jce_id: int, value: Any = None) -> bytes:
        return bytes([jce_id << 4 | cls.__jce_type__[0]])


class JceMetaclass(ModelMetaclass):

    def __new__(cls, name, bases, namespace):
        config = namespace.get("Config", BaseConfig)
        Encoder, Decoder = prepare_config(config)
        namespace.update({
            "__jce_encoder__": Encoder,
            "__jce_decoder__": Decoder
        })
        cls = super().__new__(cls, name, bases, namespace)  # type: ignore
        fields = prepare_fields(cls.__fields__)
        setattr(cls, "__jce_fields__", fields)
        return cls


class JceStruct(JceType, BaseModel, metaclass=JceMetaclass):

    if TYPE_CHECKING:
        __jce_encoder__: Type[JceEncoder]
        __jce_decoder__: Type[JceDecoder]
        __jce_fields__: Dict[str, JceModelField]

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

    # from_bytes = decode


def get_jce_type(jce_id: int) -> JceType:
    types = {
        0: BYTE,
        1: INT,
        2: INT,
        3: INT,
        4: FLOAT,
        5: DOUBLE,
        6: STRING,
        7: STRING,
        8: MAP,
        9: LIST,
        10: STRUCT_START,
        11: STRUCT_END,
        12: ZERO_TAG
    }
    return types[jce_id]


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