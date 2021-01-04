import unittest

from jce import types, JceStruct, JceField


class SsoServerInfo(JceStruct):
    server: types.STRING = JceField(jce_id=1)
    port: types.INT = JceField(jce_id=2)
    location: types.STRING = JceField(jce_id=8)
    # location: str = JceField(jce_id=8, jce_type=JceTypes.STRING)
    extra: str
    extra_default: str = "extra"


# SsoServerInfo.decode(byte, extra="1")


class TestEncode(unittest.TestCase):

    def test_struct(self):
        byte = SsoServerInfo(server="aa",
                             port=8080,
                             location="1.1.1.1",
                             extra="xxx").encode()
        print(byte.hex())


if __name__ == "__main__":
    unittest.main()
