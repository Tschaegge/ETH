from hashlib import md5, sha1, sha256, scrypt
import hmac

def onion(pw, salt, secret):
    h1 = md5(pw).digest()
    print(h1.hex())
    h2 = hmac.new(salt,h1,sha1).digest()
    print(h2.hex())
    h3 = hmac.new(secret,h2,sha256).digest()
    print(h3.hex())
    h4 = scrypt(password=h3, 
                    salt=salt, 
                    n=2**10, 
                    r=32, 
                    p=2, 
                    dklen=64)
    print(h4.hex())
    h5 = hmac.new(salt,h4,sha256).digest()
    print(h5.hex())
    return h5

PW = '6f6e696f6e732061726520736d656c6c79'
SECRET = '6275742061726520617765736f6d6520f09f988b'
SALT = '696e2061206e69636520736f6666726974746f21'

hash = onion(bytes.fromhex(PW), bytes.fromhex(SALT), bytes.fromhex(SECRET))
flag = hash.hex()
print(flag)
