#!/usr/bin/env python3
# from https://cryptohack.org/challenges/introduction/

import telnetlib
import json
from string import ascii_letters

tn = telnetlib.Telnet("aclabs.ethz.ch", 50401)
# tn = telnetlib.Telnet("localhost", 50390)

def readline():
    return tn.read_until(b"\n")

def json_recv():
    line = readline()
    return json.loads(line.decode())

def json_send(req):
    request = json.dumps(req).encode()
    tn.write(request + b"\n")
    
alreadyFound = ["00"]*15
for i in range(16):
    for el in ascii_letters:
        #Idea is to get IV encrypted, then get IV xor letter and then get IV xor letter xor letter = IV
        text = "00" *16+"".join(alreadyFound)+ el.encode().hex() + "00" * (15-i)
        request = {
        "command": "encrypt","msg": text
        }
        json_send(request)
        response2 = json_recv()
        base = response2["result"][32:64]
        secret = response2["result"][96:128]
        if base == secret:
            if alreadyFound[0] == "00":
                alreadyFound.pop(0)
            alreadyFound.append(el.encode().hex())
            break

for i in range(len(alreadyFound)):
    alreadyFound[i] = bytes.fromhex(alreadyFound[i]).decode()    


request = {"command": "flag", "solve": "".join(alreadyFound)}
response = json_send(request)
response = json_recv()
print(response["flag"])

