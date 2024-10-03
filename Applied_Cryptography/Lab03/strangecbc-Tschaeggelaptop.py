from calendar import c
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA1
from Crypto.Util.Padding import pad, unpad

class StrangeCBC():
    def __init__(self, key: bytes, iv: bytes = None, block_length: int = 16):
        """Initialize the CBC cipher.
        """

        if iv is None:
            # TODO: Pick a random IV
            iv = get_random_bytes(16)

        self.iv = iv
        self.key = key
        self.block_length = block_length

    def encrypt(self, plaintext: bytes):
        """Encrypt the input plaintext using AES-128 in strange-CBC mode:

        C_i = E_k(P_i xor C_(i-1) xor 1336)
        C_0 = IV

        Uses IV and key set from the constructor.

        Args:
            plaintext (bytes): input plaintext.

        Returns:
            bytes: ciphertext, starting from block 1 (do not include the IV)
        """
        ciphertext = b""
        c_i = self.iv
        for i in range(0, len(plaintext), 16):
            p_i = plaintext[i:i+16]
            if len(p_i) < 16:
                p_i = pad(p_i, 16)
            c_i = AES.new(self.key, AES.MODE_CBC).encrypt((a ^ b ^ 1336)for a, b in zip(p_i, c_i))
            ciphertext += c_i
            print(ciphertext)
        return ciphertext

    def decrypt(self, ciphertext: bytes):
        """Decrypt the input ciphertext using AES-128 in strange-CBC mode.

        Uses IV and key set from the constructor.

        Args:
            ciphertext (bytes): input ciphertext.

        Returns:
            bytes: plaintext.
        """
        plaintext = b""
        c_i1 = self.iv
        for i in range(0, len(ciphertext), 16):
            c_i = ciphertext[i:i+16]
            p_i = bytes((a ^ b ^ 1336) for a, b in zip(AES.new(self.key, AES.MODE_CBC).decrypt(c_i), c_i1))
            plaintext += p_i
            c_i1 = c_i
        if len(plaintext) !=0:return unpad(plaintext, 16)
        return plaintext



def main():
    cipher = StrangeCBC(get_random_bytes(16))

    # Block-aligned pts
    for pt in [bytes(range(i)) for i in range(0, 256, 16)]:
        print(cipher.decrypt(cipher.encrypt(pt)))
        #assert cipher.decrypt(cipher.encrypt(pt)) == pt

    # Non-block-aligned pts
    for pt in [bytes(range(i)) for i in range(0, 225, 15)]:
        print(cipher.decrypt(cipher.encrypt(pt)))
        #assert cipher.decrypt(cipher.encrypt(pt)) == pt

    key = bytes.fromhex("5f697180e158141c4e4bdcdc897c549a")
    iv  = bytes.fromhex("89c0d7fef96a38b051cb7ef8203dee1f")
    ct = bytes.fromhex(
            "e7fb4360a175ea07a2d11c4baa8e058d57f52def4c9c5ab"
            "91d7097a065d41a6e527db4f5722e139e8afdcf2b229588"
            "3fd46234ff7b62ad365d1db13bb249721b")
    pt = StrangeCBC(key, iv=iv).decrypt(ct)
    print(pt.decode())
    print("flag{" + SHA1.new(pt).digest().hex() + "}")

if __name__ == "__main__":
    main()
