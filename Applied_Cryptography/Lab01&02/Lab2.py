import json 
import requests

def pkcs7_pad(data, block_size):
    padding_length = block_size - (len(data) % block_size)
    padding = bytes([padding_length]) * padding_length
    return data + padding

def pkcs7_unpad(data):
    padding_length = data[-1]
    if padding_length > len(data):
        raise ValueError("Invalid padding")
    return data[:-padding_length]


pad_b = "flag".encode("utf-8")
block_size = 16
padded_flag_b = pkcs7_pad(pad_b, 16)

# Convert the padded flag to its hexadecimal representation
hex_representation = padded_flag_b.hex()
print(hex_representation)

url = "http://aclabs.ethz.ch:50220"

string = "flag, please!"
substring = [string[:i] for i in range(1, len(string)+1)]
print(substring)
for el in substring:
    encoded = el.encode()
    pad = pkcs7_pad(encoded, 16).hex()
    encrypt_payload = json.dumps({
        "command": "encrypt",
        "prepend_pad": pad
    })
    print(encrypt_payload)
    solve_payload = {
    "command": "solve",
    "ciphertext": ""
    }
    #response = requests.post(url, json=encrypt_payload)
    #ciphertext = response.json()["res"]
    #solve_payload["ciphertext"] = ciphertext

    # Send the solve request
    #response = requests.post(url, json=solve_payload)
    #print("Decrypted message:", response.text)


    
             

