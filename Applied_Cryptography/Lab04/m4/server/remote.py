#!/usr/bin/env python3
# from https://cryptohack.org/challenges/introduction/

import telnetlib
import json
from string import ascii_letters

#address = "aclabs.ethz.ch"
address = "localhost"
tn = telnetlib.Telnet(address, 50404)


def readline():
    return tn.read_until(b"\n")


def json_recv():
    line = readline()
    return json.loads(line.decode())


def json_send(req):
    request = json.dumps(req).encode()
    tn.write(request + b"\n")
    

def pad(cls, msg: bytes):
    """ Pad msg. """
    bit_padding_len = 16 - (len(msg) % 16) 
    bit_pading = b"\x00" * (bit_padding_len - 1) + b"\x01"
    return bit_pading + msg


request = {"command": "register", "user": "tschaegge", "key": "deadbeef"}
json_send(request)
response = json_recv()
print(response)

request = {"command": "list", "user": "admin"}
json_send(request)
response = json_recv()
secret_file_id = response["result"]
print(response)  

iv = "00"

request = {"command": "backup", "user": "admin", "ctxt": "00"*16}
json_send(request)
response = json_recv()
print(response)
"""request = {"command": "get", "user": "admin", "ctxt": iv + secret_file_id[0]}
json_send(request)
response = json_recv()
print(response)"""
