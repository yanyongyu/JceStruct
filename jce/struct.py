from typing import Dict, Type, TYPE_CHECKING

from pydantic import BaseModel
from pydantic.main import ModelMetaclass

from jce.encoder import JceEncoder
from jce.decoder import JceDecoder
from jce.config import BaseConfig, prepare_config
from jce.field import JceType, JceModelField, prepare_fields


# abc.ABCMeta
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


# abc.ABC
class JceStruct(JceType, BaseModel, metaclass=JceMetaclass):

    if TYPE_CHECKING:
        __jce_encoder__: Type[JceEncoder]
        __jce_decoder__: Type[JceDecoder]
        __jce_fields__: Dict[str, JceModelField]

    def encode(self):
        return self.__jce_encoder__.encode(self.__jce_fields__, self.dict())

    @classmethod
    def to_byte(cls, value):
        return cls.__jce_encoder__.encode(cls.__jce_fields__, value)

    @classmethod
    def decode(cls, data, **extra):
        return cls.__jce_decoder__.decode(cls, cls.__jce_fields__, data,
                                          **extra)
