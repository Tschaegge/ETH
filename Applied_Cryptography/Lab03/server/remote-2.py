#!/usr/bin/env python3
# from https://cryptohack.org/challenges/introduction/

import telnetlib
import json

tn = telnetlib.Telnet("aclabs.ethz.ch", 50390)
#tn = telnetlib.Telnet("localhost", 50390)

def readline():
    return tn.read_until(b"\n")

def json_recv():
    line = readline()
    return json.loads(line.decode())

def json_send(req):
    request = json.dumps(req).encode()
    tn.write(request + b"\n")

byte_literal = b"\xAA"  # Example byte literal
hex_string = byte_literal.hex()  # Convert to hexadecimal string

request = {
    "command": "hex_command",
    "hex_command": hex_string
}
json_send(request)

response = json_recv()

print(response)
