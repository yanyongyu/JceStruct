import pprint
import argparse

from jce import JceDecoder

parser = argparse.ArgumentParser(description="JceStruct command line tool")
parser.add_argument("encoded",
                    metavar="encoded",
                    type=str,
                    help="Encoded bytes in hex format")

args = parser.parse_args()
result = JceDecoder.decode_bytes(bytes.fromhex(args.encoded))

pprint.pprint(result)
