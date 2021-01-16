import unittest

from jce import types, JceDecoder


class TestDecode(unittest.TestCase):

    def test_head_encode(self):
        raw = 1
        encoded = bytes.fromhex("10")
        self.assertEqual(types.JceType.head_byte(raw, 0), encoded)

        raw = 0xAA
        encoded = bytes.fromhex("F0 AA")
        self.assertEqual(types.JceType.head_byte(raw, 0), encoded)

    def test_head_decode(self):
        raw = 1
        encoded = bytes.fromhex("10")
        self.assertEqual(JceDecoder.decode_head(encoded), (raw, 0, 1))

        raw = 0xAA
        encoded = bytes.fromhex("F0 AA")
        self.assertEqual(JceDecoder.decode_head(encoded), (raw, 0, 2))

    def test_byte_encode(self):
        raw = bytes([0xF0])
        encoded = bytes.fromhex("10 F0")
        self.assertEqual(types.BYTE.to_bytes(1, raw), encoded)

        # Zero Byte
        raw = bytes([0x00])
        encoded = bytes.fromhex("1C")
        self.assertEqual(types.BYTE.to_bytes(1, raw), encoded)

    def test_byte_decode(self):
        raw = bytes([0xF0])
        encoded = bytes.fromhex("F0")
        decoded, _ = types.BYTE.from_bytes(encoded)
        self.assertEqual(types.BYTE.validate(decoded), raw)

    def test_bool_encode(self):
        raw = True
        encoded = bytes.fromhex("10 01")
        self.assertEqual(types.BOOL.to_bytes(1, raw), encoded)

    def test_bool_decode(self):
        raw = True
        encoded = bytes.fromhex("01")
        decoded, _ = types.BOOL.from_bytes(encoded)
        self.assertEqual(types.BOOL.validate(decoded), raw)

    def test_int_encode(self):
        # int8
        raw = 127
        encoded = bytes.fromhex("10 7F")
        self.assertEqual(types.INT.to_bytes(1, raw), encoded)

        # int16
        raw = -32768
        encoded = bytes.fromhex("11 80 00")
        self.assertEqual(types.INT16.to_bytes(1, raw), encoded)

        # int32
        raw = -2147483648
        encoded = bytes.fromhex("12 80 00 00 00")
        self.assertEqual(types.INT32.to_bytes(1, raw), encoded)

        # int64
        raw = 123123123123123123
        encoded = bytes.fromhex("13 01 B5 6B D4 01 63 F3 B3")
        self.assertEqual(types.INT64.to_bytes(1, raw), encoded)

    def test_int_decode(self):
        raw = 127
        encoded = bytes.fromhex("7F")
        decoded, _ = types.BYTE.from_bytes(encoded)
        self.assertEqual(types.INT.validate(decoded), raw)

        raw = -32768
        encoded = bytes.fromhex("80 00")
        decoded, _ = types.INT16.from_bytes(encoded)
        self.assertEqual(types.INT16.validate(decoded), raw)

        raw = -2147483648
        encoded = bytes.fromhex("80 00 00 00")
        decoded, _ = types.INT32.from_bytes(encoded)
        self.assertEqual(types.INT32.validate(decoded), raw)

        raw = 123123123123123123
        encoded = bytes.fromhex("01 B5 6B D4 01 63 F3 B3")
        decoded, _ = types.INT64.from_bytes(encoded)
        self.assertEqual(types.INT64.validate(decoded), raw)


if __name__ == "__main__":
    unittest.main()
