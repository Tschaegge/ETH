import hashlib
import hmac
from string import ascii_lowercase

def hmac_sha1(key, message):
    """
    Generate HMAC-SHA1 hash.
    
    Parameters:
        key (bytes): The key used for the HMAC.
        message (bytes): The message to be authenticated.
        
    Returns:
        bytes: The HMAC-SHA1 hash.
    """
    hmac_sha1 = hmac.new(key, message, hashlib.sha1)
    return hmac_sha1.digest()

SALT = "b49d3002f2a089b371c3"
HASH = "d262db83f67a37ff672cf5e1d0dfabc696e805bc"
for letter1 in ascii_lowercase:
    for letter2 in ascii_lowercase:
        for letter3 in ascii_lowercase:
            for letter4 in ascii_lowercase:
                for letter5 in ascii_lowercase:
                    for letter6 in ascii_lowercase:
                        word = letter1 + letter2 + letter3 + letter4 + letter5 + letter6
                        if hmac_sha1(word.encode(),bytes.fromhex(SALT)).hex() == HASH:
                            print(word)
                            exit(0)
    
