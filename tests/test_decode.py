import unittest

from jce import types, JceStruct, JceField


class SsoServerInfo(JceStruct):
    server: types.STRING = JceField(jce_id=1)
    port: types.INT = JceField(jce_id=2)
    location: types.STRING = JceField(jce_id=8)
    # location: str = JceField(jce_id=8, jce_type=types.STRING)
    extra: str
    extra_default: str = "extra"


class TestDecode(unittest.TestCase):

    def test_struct(self):
        a = SsoServerInfo.decode(
            bytes.fromhex("16 04 72 63 6e 62 21 1f 40 86 04 72 63 6e 62"),
            extra="xxx")
        b = SsoServerInfo(server="rcnb",
                          port=8000,
                          location="rcnb",
                          extra="xxx")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
