#!/usr/bin/env python3
# from https://cryptohack.org/challenges/introduction/

import telnetlib
import json
from string import ascii_letters

address = "aclabs.ethz.ch"
tn = telnetlib.Telnet(address, 50403)


def readline():
    return tn.read_until(b"\n")


def json_recv():
    line = readline()
    return json.loads(line.decode())


def json_send(req):
    request = json.dumps(req).encode()
    tn.write(request + b"\n")


# Generates all 6 IV chains
ivs = [[] for _ in range(6)]
j = 0
while j < 6:
    request = {"command": "encrypt", "msg": ""}
    json_send(request)
    response = json_recv()
    iv = response["iv"]
    if all(iv != ivs[k][0] for k in range(j)):
        ivs[j].append(iv)
        # If the secret message is ZZZZ...Z, then we need 1+6+52*2*32 many encrytion querries
        for i in range(1 + 6 + 52 * 2 * 32):
            request = {"command": "encrypt", "msg": ""}
            json_send(request)
            response = json_recv()
            iv = response["iv"]
            ivs[j].append(iv)
        j += 1
    tn.close()
    tn.open(address, 50403)


def restoreCharacters(i, j, k, alreadyFound: list):
    for char in ascii_letters:
        request = {
            "command": "encrypt",
            "msg": ivs[j][i] + "".join(alreadyFound) + char.encode("utf-8").hex(),
        }
        i += 1
        json_send(request)
        response = json_recv()
        ctxt1 = response["ctxt"][:96]
        request = {
            "command": "encrypt",
            "msg": ivs[j][i] + bytes(31 - k).hex(),
        }
        i += 1
        json_send(request)
        response = json_recv()
        ctxt2 = response["ctxt"][:96]
        if ctxt1 == ctxt2:
            break
    if alreadyFound[0] == "00":
        alreadyFound.pop(0)
    alreadyFound.append(char.encode("utf-8").hex())
    return i

i = 0

request = {"command": "encrypt", "msg": ""}
i += 1
json_send(request)
response = json_recv()
iv = response["iv"]

for j in range(6):
    if iv == ivs[j][i - 1]:
        break

alreadyFound = ["00"] * 31
for k in range(32):
    i = restoreCharacters(i, j, k, alreadyFound)

print(alreadyFound)
sol = ""
for el in alreadyFound:
    sol += bytes.fromhex(el).decode("utf-8")


print(sol)
request = {"command": "guess", "guess": sol}
json_send(request)
response = json_recv()
print(response)
print(response["flag"])
