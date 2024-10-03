#!/usr/bin/env python3
# from https://cryptohack.org/challenges/introduction/

import telnetlib
import json

from string import ascii_letters

tn = telnetlib.Telnet("aclabs.ethz.ch", 50400)
#tn = telnetlib.Telnet("localhost", 50400)


def xor(x: bytes, y: bytes):
    return bytes(a ^ b for a, b in zip(x, y))

def readline():
    return tn.read_until(b"\n")


def json_recv():
    line = readline()
    return json.loads(line.decode())


def json_send(req):
    request = json.dumps(req).encode()
    tn.write(request + b"\n")

#Counter is implemented wrong if the message is not a full block, you can encrypt with the same onetime pad twice
a_string = "a" * 15

request = {"command": "encrypt", "msg": a_string}

json_send(request)

response = json_recv()


request2 = {
    "command": "encrypt_secret",
}

json_send(request2)

response2 = json_recv()


enc1 = bytes.fromhex(response["result"])
enc2 = bytes.fromhex(response2["result"])

xor1 = xor(enc1, enc2)
sol1 = xor(xor1, a_string.encode("utf-8"))


request = {"command":"encrypt", "msg":a_string}
json_send(request)
response = json_recv()
enc1 = bytes.fromhex(response["result"])
enc2 = bytes.fromhex(response2["result"])[-14:]
xor1 = xor(enc1, enc2)
sol2 = xor(xor1, a_string.encode("utf-8"))

for el in ascii_letters:
    #we decrypted first 15 and the last 14 bytes of the secret, so we guess the 16th byte
    sol = sol1[-7:].decode("utf-8") +el+ sol2[:8].decode("utf-8")

    request3 = {"command": "flag", "solve": sol}

    json_send(request3)

    response3 = json_recv()

    if "flag" in response3:
        print(response3["flag"])
        break
