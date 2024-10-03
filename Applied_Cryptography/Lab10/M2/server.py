from boilerplate import CommandServer, on_command

from secrets import randbelow, token_bytes

from Crypto.Hash import SHA256
from Crypto.PublicKey import DSA

class SchnorrSignatureScheme:
    def __init__(self, key: DSA.DsaKey):
        self._key = key
        assert self._key.q.bit_length() % 8 == 0
        assert self._key.p.bit_length() % 8 == 0
        self._q_bytes = self._key.q.bit_length() // 8
        self._p_bytes = self._key.p.bit_length() // 8

    def sign(self, msg: bytes) -> bytes:
        p, q, g, x = self._key.p, self._key.q, self._key.g, self._key.x
        p_bytes, q_bytes = self._p_bytes, self._q_bytes

        k = randbelow(q) + 1
        r = pow(g, k, p)
        data = r.to_bytes(p_bytes, 'big') + msg
        e_b = SHA256.new(data=data).digest()[:q_bytes]

        e = int.from_bytes(e_b, 'big')
        s = (k - x * e) % q

        return s.to_bytes(q_bytes, 'big') + e_b

    def verify(self, msg, signature):
        p, g, y = self._key.p, self._key.g, self._key.y
        p_bytes, q_bytes = self._p_bytes, self._q_bytes

        s_b, e_b = signature[:q_bytes], signature[q_bytes:]
        s, e = int.from_bytes(s_b, 'big'), int.from_bytes(e_b, 'big')

        r_v = pow(g, s, p) * pow(y, e, p) % p
        data = r_v.to_bytes(p_bytes, 'big') + msg
        e_b_v = SHA256.new(data=data).digest()[:q_bytes]

        if e_b_v != e_b:
            raise ValueError("Signature verification failed")

    @classmethod
    def new(cls, key: DSA.DsaKey):
        return SchnorrSignatureScheme(key)


class BeaconServer(CommandServer):
    def __init__(self, flag, *args, **kwargs):
        self.flag = flag
        self.planet_db = dict()

        self.fingerprint_len = 2

        super().__init__(*args, **kwargs)

    @on_command("new_planet")
    def handle_new_planet(self, _):
        try:
            key = DSA.generate(1024)
            signer = SchnorrSignatureScheme.new(key)

            planet_name = token_bytes(8).hex()

            # this little maneuver's gonna cost you 51 years
            key_serialized = key.public_key().export_key()
            fingerprint = SHA256.new(data=key_serialized).digest()[:self.fingerprint_len]

            status = "expedition started"
            signature = signer.sign(status.encode() + fingerprint)
            self.planet_db[planet_name] = signature

            self.send_message({"planet": planet_name, "status": status, "signature": signature.hex(), "key": key_serialized.hex()})
        except (KeyError, ValueError, TypeError) as e:
            self.send_message({"error": f"Invalid parameters. {type(e).__name__}: {e}"})

    @on_command("signal_planet")
    def handle_signal(self, msg):
        try:
            name = msg["planet"]
            key = bytes.fromhex(msg["key"])
            signature = bytes.fromhex(msg["signature"])

            key = DSA.import_key(key)
            verifier = SchnorrSignatureScheme.new(key)
            fingerprint = SHA256.new(data=key.public_key().export_key()).digest()[:self.fingerprint_len]

            # Only the original registrar of a planet can change its habitable status.
            # Use signatures to enforce this!
            verifier.verify("expedition started".encode() + fingerprint, self.planet_db[name])

            # Check also that the message contains an authentic signature for the message
            # "this planet is good"
            status = "this planet is good"
            verifier.verify(status.encode() + fingerprint, signature)

            self.send_message({"flag": self.flag})
        except (KeyError, ValueError, TypeError) as e:
            self.send_message({"error": f"Invalid parameters. {type(e).__name__}: {e}"})

if __name__ == "__main__":
    flag = "flag{test_flag}"
    BeaconServer.start_server("0.0.0.0", 51002, flag=flag)
