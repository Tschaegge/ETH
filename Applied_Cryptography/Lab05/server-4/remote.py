#!/usr/bin/env python3

import json
import socket

# =====================================================================================
#   Config Variables (Change as needed)
# =====================================================================================

# Remember to change the port if you are reusing this client for other challenges
PORT = 50501

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

from passlib.hash import argon2

def pw_hash(pw):
  return argon2.hash(bytes.fromhex(pw))

password = run_command({"command": "password"})
print(password)
flag = run_command({"command": "guess", "guess": pw_hash(password["res"])})
print(flag)


