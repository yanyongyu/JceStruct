import abc
from typing import Any, Dict, Type, TypeVar, Optional

from pydantic import Field
from pydantic.typing import NoArgAnyCallable
from pydantic.fields import Undefined, ModelField

T = TypeVar("T", bound="JceType")


class JceType(abc.ABC):

    @abc.abstractmethod
    @classmethod
    def to_byte(cls: Type[T], value: T):
        raise NotImplementedError


# TODO: to_byte
class JceTypes:

    class BYTE(JceType, bytes):
        pass

    class INT16(JceType, int):
        pass


def JceField(
    default: Any = Undefined,
    *,
    jce_id: int,
    jce_type: Optional[JceType] = None,
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

    def __init__(self, jce_id: int, jce_type: Type[JceType]):
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
