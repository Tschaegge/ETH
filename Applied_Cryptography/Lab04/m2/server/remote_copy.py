#!/usr/bin/env python3
# from https://cryptohack.org/challenges/introduction/

import telnetlib
import json
from string import ascii_letters

#tn = telnetlib.Telnet("aclabs.ethz.ch", 50402)
tn = telnetlib.Telnet("localhost", 50402)

def readline():
    return tn.read_until(b"\n")

def json_recv():
    line = readline()
    return json.loads(line.decode())

def json_send(req):
    request = json.dumps(req).encode()
    tn.write(request + b"\n")


request = {"command": "encrypt", "msg": ""}
json_send(request)
response = json_recv()
print(response)
