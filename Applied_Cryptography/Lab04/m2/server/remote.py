#!/usr/bin/env python3
# from https://cryptohack.org/challenges/introduction/

import telnetlib
import json
from string import ascii_letters

tn = telnetlib.Telnet("aclabs.ethz.ch", 50402)


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
j=0
while j<6:
    request = {"command": "encrypt", "msg": ""}
    json_send(request)
    response = json_recv()
    iv = response["iv"]
    if all(iv != ivs[k][0] for k in range(j)):
        ivs[j].append(iv)
        #1000 is an arbitrary number but it should be enough even in really unlucky cases
        for i in range(1000):
            request = {"command": "encrypt", "msg": ""}
            json_send(request)
            response = json_recv()
            iv = response["iv"]
            ivs[j].append(iv)
        j+=1
    tn.close()
    tn.open("aclabs.ethz.ch", 50402)    


MESSAGES = [
    "Pad to the left",
    "Unpad it back now y'all",
    "Game hop this time",
    "Real world, let's stomp!",
    "Random world, let's stomp!",
    "AES real smooth~"
]
MESSAGES = [
    msg.ljust(32) for msg in MESSAGES
]


def restoreMessage(i):
    #This request finds the IV chain that is used for the next message
    request = {"command": "encrypt", "msg": ""}
    i += 1
    json_send(request)
    response = json_recv()
    iv = response["iv"]
    j = 0
    for j in range(6):
        if iv == ivs[j][i-1]:
            break
    #We send the IV such that we encrypt 0
    request = {"command": "encrypt", "msg": ivs[j][i]}
    i+=1
    json_send(request)
    response = json_recv()
    ctxt1 = response["ctxt"][:96]
    for m in MESSAGES:
        #We encrypt 0 and if m is the same as the secret message, the first 3 blocks of the ciphertext will be the same
        mes = (bytes.fromhex(ivs[j][i]) + m.encode()).hex()
        i+=1
        request = {"command": "encrypt", "msg": mes}
        json_send(request)
        response = json_recv()
        ctxt2 = response["ctxt"][:96]
        if ctxt1 == ctxt2:

            break
    return i,m


i = 0
#Do this 64 times to get the flag
for _ in range(64):
    i,m = restoreMessage(i)
    request = {"command": "guess", "guess": m}
    json_send(request)
    response = json_recv()

request = {"command": "flag"}
json_send(request)
response = json_recv()
print(response["flag"])
