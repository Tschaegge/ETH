#!/usr/bin/env python3

import json
import socket
from Crypto.Util.Padding import pad, unpad
from string import ascii_letters, digits

Alphabet = ascii_letters+digits

# =====================================================================================
#   Config Variables (Change as needed)
# =====================================================================================

# Remember to change the port if you are reusing this client for other challenges
PORT = 50221

# Change this to REMOTE = False if you are running against a local instance of the server
REMOTE = True

# Remember to change this to graded.aclabs.ethz.ch if you use this for graded labs
HOST = "aclabs.ethz.ch"

# =====================================================================================
#   Client Boilerplate (Do not touch, do not look)
# =====================================================================================

fd = socket.create_connection((HOST if REMOTE else "localhost", PORT)).makefile("rw")

def run_command(command):
    """Serialize `command` to JSON and send to the server, then deserialize the response"""
    fd.write(json.dumps(command) + "\n")
    fd.flush()
    return json.loads(fd.readline())

# ===================================================================================
#    Write Your Solution Below
# ===================================================================================
def pkcs7_pad(data, block_size):
    padding_length = block_size - (len(data) % block_size)
    padding = bytes([padding_length]) * padding_length
    return data + padding

def pkcs7_unpad(data):
    padding_length = data[-1]
    if padding_length > len(data):
        raise ValueError("Invalid padding")
    return data[:-padding_length]


string = ""
encrypt_payload = {
    "command": "encrypt",
    "prepend_pad": string
}
res = run_command(encrypt_payload)["res"]
print(res)
print(len(res))
length = len(res)
while True: #do while functionality
    string+= "aa"
    encrypt_payload = {
        "command": "encrypt",
        "prepend_pad": string
    }
    res = run_command(encrypt_payload)["res"]
    newLength = len(res)
    
    if newLength >length:
        break
print(res)
sol = res[32:]
print(sol)
for el in Alphabet:
    p = pad(el.encode("utf-8"), 16).hex()
    encrypt_payload = {
        "command": "encrypt",
        "prepend_pad": p
    }
    #print(encrypt_payload)
    res = run_command(encrypt_payload)["res"][:32]   
    print(res)
    if res == sol:
        print("lol",el)
        break


