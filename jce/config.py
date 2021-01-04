from typing import Type, Tuple

from jce.log import logger
from jce.encoder import JceEncoder
from jce.decoder import JceDecoder


class BaseConfig:
    jce_encoder = JceEncoder
    jce_decoder = JceDecoder


def prepare_config(config: object) -> Tuple[Type[JceEncoder], Type[JceDecoder]]:
    Encoder = getattr(config, "jce_encoder", JceEncoder)
    Decoder = getattr(config, "jce_decoder", JceDecoder)
    if Encoder is not JceEncoder and not issubclass(Encoder, JceEncoder):
        raise TypeError(f"Encoder {Encoder} is not a valid encoder")
    if Decoder is not JceDecoder and not issubclass(Decoder, JceDecoder):
        raise TypeError(f"Decoder {Decoder} is not a valid decoder")
    return Encoder, Decoder
