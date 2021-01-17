import unittest
from typing import Dict

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
        encoded = bytes.fromhex("10 F0")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.BYTE.validate(decoded), raw)

    def test_bool_encode(self):
        raw = True
        encoded = bytes.fromhex("10 01")
        self.assertEqual(types.BOOL.to_bytes(1, raw), encoded)

        raw = False
        encoded = bytes.fromhex("1C")
        self.assertEqual(types.BOOL.to_bytes(1, raw), encoded)

    def test_bool_decode(self):
        raw = True
        encoded = bytes.fromhex("10 01")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.BOOL.validate(decoded), raw)

        raw = False
        encoded = bytes.fromhex("1C")
        _, decoded, _ = JceDecoder.decode_single(encoded)
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
        encoded = bytes.fromhex("10 7F")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.INT.validate(decoded), raw)

        raw = -32768
        encoded = bytes.fromhex("11 80 00")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.INT16.validate(decoded), raw)

        raw = -2147483648
        encoded = bytes.fromhex("12 80 00 00 00")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.INT32.validate(decoded), raw)

        raw = 123123123123123123
        encoded = bytes.fromhex("13 01 B5 6B D4 01 63 F3 B3")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.INT64.validate(decoded), raw)

    def test_float_encode(self):
        raw = 81.5
        encoded = bytes.fromhex("14 42 A3 00 00")
        self.assertEqual(types.FLOAT.to_bytes(1, raw), encoded)

        raw = 456.2
        encoded = bytes.fromhex("15 40 7C 83 33 33 33 33 33")
        self.assertEqual(types.DOUBLE.to_bytes(1, raw), encoded)

    def test_float_decode(self):
        raw = 81.5
        encoded = bytes.fromhex("14 42 A3 00 00")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.FLOAT.validate(decoded), raw)

        raw = 456.2
        encoded = bytes.fromhex("15 40 7C 83 33 33 33 33 33")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.DOUBLE.validate(decoded), raw)

    def test_string_encode(self):
        raw = "Hello"
        encoded = bytes.fromhex("16 05 48 65 6C 6C 6F")
        self.assertEqual(types.STRING1.to_bytes(1, raw), encoded)

        raw = "Hello" * 100
        encoded = bytes.fromhex("17 00 00 01 F4" + "48 65 6C 6C 6F" * 100)
        self.assertEqual(types.STRING4.to_bytes(1, raw), encoded)

    def test_string_decode(self):
        raw = "Hello"
        encoded = bytes.fromhex("16 05 48 65 6C 6C 6F")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.STRING1.validate(decoded), raw)

        raw = "Hello" * 100
        encoded = bytes.fromhex("17 00 00 01 F4" + "48 65 6C 6C 6F" * 100)
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.STRING4.validate(decoded), raw)

    def test_map_encode(self):
        raw: Dict[types.JceType, types.JceType] = {
            types.STRING1("one"): types.STRING1("foo"),
            types.STRING1("two"): types.STRING1("bar")
        }
        encoded = bytes.fromhex("18 00 02 06 03 6F 6E 65 16 03 66 "
                                "6F 6F 06 03 74 77 6F 16 03 62 61 72")
        self.assertEqual(types.MAP.to_bytes(1, raw), encoded)

        raw: Dict[types.JceType, types.JceType] = {
            types.STRING1("one"):
                types.MAP({types.STRING1("two"): types.BYTES("foo".encode())})
        }
        encoded = bytes.fromhex("18 00 01 06 03 6F 6E 65 18 00 01 "
                                "06 03 74 77 6F 1D 00 00 03 66 6F 6F")
        self.assertEqual(types.MAP.to_bytes(1, raw), encoded)

    def test_map_decode(self):
        raw: Dict[types.JceType, types.JceType] = {
            types.STRING1("one"): types.STRING1("foo"),
            types.STRING1("two"): types.STRING1("bar")
        }
        encoded = bytes.fromhex("18 00 02 06 03 6F 6E 65 16 03 66 "
                                "6F 6F 06 03 74 77 6F 16 03 62 61 72")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.MAP.validate(decoded), raw)

        raw: Dict[types.JceType, types.JceType] = {
            types.STRING1("one"):
                types.MAP({types.STRING1("two"): types.BYTES("foo".encode())})
        }
        encoded = bytes.fromhex("18 00 01 06 03 6F 6E 65 18 00 01 "
                                "06 03 74 77 6F 1D 00 00 03 66 6F 6F")
        _, decoded, _ = JceDecoder.decode_single(encoded)
        self.assertEqual(types.MAP.validate(decoded), raw)


if __name__ == "__main__":
    unittest.main()
