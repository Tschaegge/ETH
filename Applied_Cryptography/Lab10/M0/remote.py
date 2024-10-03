#!/usr/bin/env python3

import json
import socket

# =====================================================================================
#   Config Variables (Change as needed)
# =====================================================================================

# Remember to change the port if you are reusing this client for other challenges
PORT = 51000

# Change this to REMOTE = False if you are running against a local instance of the server
REMOTE = False

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


params = run_command({"command": "get_rand_params"})
g,p,q,h = params["g"], params["p"], params["q"], params["h"]
print(run_command({"command": "contribute_randomness", "random": q*(p-1)})) #We multiply with q*(p-1) to get (p-1)*(p-1)=1 

params2 = run_command({"command": "get_rand_params"})
print(params2)
