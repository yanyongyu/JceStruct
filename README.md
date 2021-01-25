# Jce Struct

Tencent JCE Encode/Decode with fully pydantic support

## Installation

```bash
pip install JceStruct
```

or install from source (using poetry)

```bash
poetry add git+https://github.com/yanyongyu/JceStruct.git
```

or clone and install

```bash
git clone https://github.com/yanyongyu/JceStruct.git
cd JceStruct
poetry install
```

## Usage

### Create Struct

Create your struct by inheriting `JceStruct` and define your fields with `JceField`

```python
from jce import types, JceStruct, JceField


class ExampleStruct(JceStruct):
    field1: types.INT32 = JceField(jce_id=1)
    field2: float = JceField(jce_id=2, jce_type=types.DOUBLE)  # define type in options
    field3: types.LIST[OtherStruct] = JceField(jce_id=3)  # nested struct supported
    extra_pydantic_field: str = "extra_pydantic_field"  # other field is optional
```

### Encode/Decode

```python
# simple encode decode
raw: ExampleStruct = ExampleStruct.decode(bytes, extra_pydantic_field="extra")
bytes = raw.encode()

# decode list from example struct
raw = OtherStruct.decode_list(bytes, jce_id=3, **extra)
```

### Custom Encoder/Decoder

Just inherit JceEncoder/JceDecoder and add it to your struct configuration

```python
from jce import JceStruct, JceEncoder


class CustomEncoder(JceEncoder):
    pass


class ExampleStruct(JceStruct):

    class Config:
        jce_encoder = CustomEncoder
        # jce_decoder = CustomDecoder
```

### Custom types

Just inherit JceType and implement abstruct methods

```python
from jce import types


class CustomType(types.JceType):
    ...
```

### Change default types

By default, head bytes are treated like this:

```python
{
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
    12: ZERO_TAG,
    13: BYTES
}
```

field will be converted to the type defined in struct when validate.

to change it:

```python
class ExampleStruct(JceStruct):

    class Config:
        jce_default_type = {
            # add all types here
        }
```
