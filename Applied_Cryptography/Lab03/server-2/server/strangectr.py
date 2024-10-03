from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA1
from Crypto.Util.Padding import pad, unpad

class StrangeCTR():
    def __init__(self, key: bytes, nonce : bytes = None, initial_value : int = 0, block_length: int = 16):
        """Initialize the CTR cipher.
        """

        if nonce is None:
            # Pick a random nonce
            nonce = get_random_bytes(block_length//2)

        self.nonce = nonce
        self.initial_value = initial_value
        self.key = key
        self.block_length = block_length

    def encrypt(self, plaintext: bytes):
        """Encrypt the input plaintext using AES-128 in strange-CTR mode:

        C_i = E_k(N || c(i)) xor P_i xor 1337

        Uses nonce, counter initial value and key set from the constructor.

        Args:
            plaintext (bytes): input plaintext.

        Returns:
            bytes: ciphertext
        """
        integer = 1337
        plaintext = pad(plaintext, self.block_length)
        counter = self.nonce + self.initial_value.to_bytes(self.block_length - self.block_length//2, "big")
        ciphertext = b""
        for i in range(0, len(plaintext), self.block_length):
            encryption = AES.new(self.key, AES.MODE_ECB).encrypt(counter)
            xor = bytes(a^b^c for a,b,c in zip(encryption, plaintext[i:i+self.block_length] , integer.to_bytes(self.block_length, "big")))
            ciphertext += xor
            counter_int = int.from_bytes(counter, byteorder='big')  # Convert bytes to integer
            counter_int += 1  # Increment the integer counter
            # Convert the incremented integer back to bytes
            counter = counter_int.to_bytes((counter_int.bit_length() + 7) // 8, byteorder='big')
        return ciphertext

    def decrypt(self, ciphertext: bytes):
        """Decrypt the input ciphertext using AES-128 in strange-CTR mode.

        Uses nonce, counter initial value and key set from the constructor.

        Args:
            ciphertext (bytes): input ciphertext.

        Returns:
            bytes: plaintext.
        """
        integer = 1337
        counter = self.nonce + self.initial_value.to_bytes(
            self.block_length - self.block_length // 2, "big"
        )
        plaintext = b""
        for i in range(0, len(ciphertext), self.block_length):
            encryption = AES.new(self.key, AES.MODE_ECB).encrypt(counter)
            xor = bytes(
                a ^ b ^ c
                for a, b, c in zip(
                    encryption,
                    ciphertext[i : i + self.block_length],
                    integer.to_bytes(self.block_length, "big"),
                )
            )
            plaintext += xor
            counter_int = int.from_bytes(
                counter, byteorder="big"
            )  # Convert bytes to integer
            counter_int += 1  # Increment the integer counter
            # Convert the incremented integer back to bytes
            counter = counter_int.to_bytes(
                (counter_int.bit_length() + 7) // 8, byteorder="big"
            )
        return unpad(plaintext,self.block_length)

def main():
    cipher = StrangeCTR(get_random_bytes(16))

    # Block-aligned pts
    for pt in [bytes(range(i)) for i in range(0, 256, 16)]:
        assert cipher.decrypt(cipher.encrypt(pt)) == pt

    # Non-block-aligned pts
    for pt in [bytes(range(i)) for i in range(0, 225, 15)]:
        assert cipher.decrypt(cipher.encrypt(pt)) == pt

    plain = pad(b"intro",16)
    cipher = bytes.fromhex("01f0ceb3dad5f9cd23293937c893e0ec")
    key = bytes(a^b for a,b in zip(plain,cipher))
    print(key)
    plain2 = pad(b"flag",16)
    print(bytes(a^b for a,b in zip(plain2,key)).hex())

if __name__ == "__main__":
    main()
