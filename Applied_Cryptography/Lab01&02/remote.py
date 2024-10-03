#!/usr/bin/env python3

import json
import socket

# =====================================================================================
#   Config Variables (Change as needed)
# =====================================================================================

# Remember to change the port if you are reusing this client for other challenges
PORT = 50220

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


string = "flag, please!"
#string = "aaaaaaaaa"
#substring = [string[:i] for i in range(1, len(string)+1)]
#for el in substring:
encoded = string.encode()
pad = pkcs7_pad(encoded,16).hex()
#pad = encoded.hex()
encrypt_payload = {
    "command": "encrypt",
    "prepend_pad": pad
}
print(encrypt_payload)
sol = run_command(encrypt_payload)
print(sol)
res = sol["res"]
res = res[:32]
print(res)
solve_payload = {
"command": "solve",
"ciphertext": res
}
response = run_command(solve_payload)
print(response)



