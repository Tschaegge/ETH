import base64
import html  # standard Library
from Crypto.Hash import SHA256
import requests
import json
import dns_server as ds
import challenge_HTTP_server
import challenge_HTTP_server as hs
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from dns_server import Dns_Server
from time import sleep


"""The first phase of ACME is for the client to request an account with
   the ACME server.  The client generates an asymmetric key pair and
   requests a new account, optionally providing contact information,
   agreeing to terms of service (ToS), and/or associating the account
   with an existing account in another system.  The creation request is
   signed with the generated private key to prove that the client
   controls it. (Quoted from RFC8555)"""
   
   #Nondeterminism Check


class acme_client:
    def __init__(self, dir):
        self.dir = dir
        self.privateKey, self.publicKey, self.signer = self.getKeys()
        self.urls = {}
        self.finalize = None
        self.domains = []
        self.domainChallenge = {}
        self.nonce = None
        self.myaccount = None
        self.orderUrl = None
        self.authorizations = []
        self.challenges = []
        self.challengeUrl = []
        self.certificateUrl = None
        self.dns = Dns_Server("", "")
        self.certificate = None

    def getKeys(self):
        """We use ECC to generate keys as an ACME server must implement ES256"""
        private_key = ECC.generate(curve="p256")
        f = open("myprivatekey.pem", "wt")
        f.write(private_key.export_key(format="PEM"))  # type: ignore
        f.close()

        public_key = private_key.public_key()
        f = open("mypublickey.pem", "wt")
        f.write(public_key.export_key(format="PEM"))  # type: ignore
        f.close()

        signer = DSS.new(private_key, "fips-186-3")

        return private_key, public_key, signer

    def generate_b64(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

    def firstRequest(self):
        request = requests.get(self.dir, verify="./pebble.minica.pem")
        data = request.text
        print("Data:" + data)
        return request

    def populateUrls(self):
        response = self.firstRequest().json()
        self.urls.update(response)
        print(self.urls)

    def getNonce(self):
        request = requests.head(self.urls["newNonce"], verify="pebble.minica.pem")
        self.nonce = request.headers["Replay-Nonce"]
        print("nonce")
        return self.nonce

    def get_jwk(self):
        jwk = {
            "kid": "0",
            "kty": "EC",
            "crv": "P-256",
            "x": self.generate_b64(self.privateKey.pointQ.x.to_bytes()),  # type: ignore
            "y": self.generate_b64(self.privateKey.pointQ.y.to_bytes()),  # type: ignore
        }
        return jwk

    def key_authorization(self, token):
        key = {
            "crv": "P-256",
            "kty": "EC",
            "x": self.generate_b64(self.privateKey.pointQ.x.to_bytes()),  # type: ignore
            "y": self.generate_b64(self.privateKey.pointQ.y.to_bytes()),  # type: ignore
        }
        hash = self.generate_b64(
            SHA256.new(
                str.encode(json.dumps(key, separators=(",", ":")), encoding="utf-8")
            ).digest()
        )
        return f"{token}.{hash}"

    def create_account(self):
        payload = {"termsOfServiceAgreed": True}

        encoded_payload = self.generate_b64(json.dumps(payload))

        protected = {
            "alg": "ES256",
            "nonce": self.getNonce(),
            "url": self.urls["newAccount"],
            "jwk": self.get_jwk(),
        }
        encoded_protected = self.generate_b64(json.dumps(protected))
        data = f"{encoded_protected}.{encoded_payload}".encode("ascii")
        hash = SHA256.new(data)
        signature = self.signer.sign(hash)

        message = {
            "protected": encoded_protected,
            "payload": encoded_payload,
            "signature": self.generate_b64(signature),
        }
        header = {"Content-type": "application/jose+json"}
        request = requests.post(
            self.urls["newAccount"],
            headers=header,
            data=json.dumps(message),
            verify="./pebble.minica.pem",
        )
        requestData = request.text
        print("Data2:" + requestData)
        self.myaccount = request.headers["Location"]
        self.nonce = request.headers["Replay-Nonce"]

    def submit_order(self, domains):
        self.domains = domains
        payload = {
            "identifiers": [{"type": "dns", "value": domain} for domain in domains]
        }
        encoded_payload = self.generate_b64(json.dumps(payload))

        protected = {
            "alg": "ES256",
            "nonce": self.nonce,
            "kid": self.myaccount,
            "url": self.urls["newOrder"],
        }
        encoded_protected = self.generate_b64(json.dumps(protected))

        data = f"{encoded_protected}.{encoded_payload}".encode("ascii")
        hash = SHA256.new(data)
        signature = self.signer.sign(hash)

        message = {
            "protected": encoded_protected,
            "payload": encoded_payload,
            "signature": self.generate_b64(signature),
        }
        header = {"Content-type": "application/jose+json"}
        request = requests.post(
            self.urls["newOrder"],
            headers=header,
            data=json.dumps(message),
            verify="./pebble.minica.pem",
        )
        print("order", request.status_code, request.content, request.headers)

        self.orderUrl = request.headers["Location"]
        self.nonce = request.headers["Replay-Nonce"]
        reqJson = request.json()
        self.finalize = reqJson["finalize"]
        self.authorizations = reqJson["authorizations"]

    def get_challenge(self, type):
        type = type[:-2] + "-" + type[-2:]
        for authorization in self.authorizations:
            payload = ""
            protected = {
                "alg": "ES256",
                "nonce": self.nonce,
                "kid": self.myaccount,
                "url": authorization,
            }
            encoded_protected = self.generate_b64(json.dumps(protected))

            data = f"{encoded_protected}.{payload}".encode("ascii")
            hash = SHA256.new(data)
            signature = self.signer.sign(hash)

            message = {
                "protected": encoded_protected,
                "payload": payload,
                "signature": self.generate_b64(signature),
            }
            header = {"Content-type": "application/jose+json"}
            request = requests.post(
                authorization,
                headers=header,
                data=json.dumps(message),
                verify="./pebble.minica.pem",
            )
            print("challenge", request.status_code, request.content, request.headers)
            self.nonce = request.headers["Replay-Nonce"]
            reqJson = request.json()
            for challenge in reqJson["challenges"]:
                print("chllenges", challenge)
                print("authorization" + str(authorization))
                challenge["authorization"] = authorization
                print(type, " == ", challenge["type"])
                if type == challenge["type"]:
                    self.challenges.append(challenge)
                    self.domainChallenge[challenge["url"]] = reqJson["identifier"][
                        "value"
                    ]
                    print("challenges1", self.challenges)

    def execute_challenge(self, type, record):
        type = type[:-2] + "-" + type[-2:]
        print(f"{type} == http-01 ")
        if type == "http-01":
            self.execute_http(type, record)
        else:  # type is dns
            self.execute_dns(type, record)

    def execute_dns(self, type, record):
        self.dns.stop_server()
        encoded_auth_keys = []

        for challenge in self.challenges:
            authorization_key = self.key_authorization(challenge["token"])
            print(type)
            self.challengeUrl.append(challenge["url"])
            hash = SHA256.new(str.encode(authorization_key, encoding="ascii")).digest()
            encoded_auth_key = self.generate_b64(hash)
            encoded_auth_keys.append(encoded_auth_key)
        zone = ""

        for encoded_auth_key, challenge in zip(encoded_auth_keys, self.challengeUrl):
            rec = f'_acme-challenge.{self.domainChallenge[challenge]}. 300 IN TXT "{encoded_auth_key}"'
            zone += rec + "\n"
        print(zone)
        self.dns = Dns_Server(zone, record)
        self.dns.start_server()

        for challenge in self.challenges:
            print("challenge1 ", challenge)
            url = challenge["url"]
            payload = {}
            encoded_payload = self.generate_b64(json.dumps(payload))
            protected = {
                "alg": "ES256",
                "nonce": self.nonce,
                "kid": self.myaccount,
                "url": url,
            }
            encoded_protected = self.generate_b64(json.dumps(protected))

            data = f"{encoded_protected}.{encoded_payload}".encode("ascii")
            hash = SHA256.new(data)
            signature = self.signer.sign(hash)

            message = {
                "protected": encoded_protected,
                "payload": encoded_payload,
                "signature": self.generate_b64(signature),
            }
            header = {"Content-type": "application/jose+json"}
            request = requests.post(
                url,
                headers=header,
                data=json.dumps(message),
                verify="./pebble.minica.pem",
            )
            print(
                "execute_dns",
                request.status_code,
                request.content,
                request.headers,
            )
            self.nonce = request.headers["Replay-Nonce"]
            # url = challenge["authorization"]
            print("testurl" + url)

        for challenge in self.challenges:
            url = challenge["url"]
            for i in range(5):
                payload = ""
                protected = {
                    "alg": "ES256",
                    "nonce": self.nonce,
                    "kid": self.myaccount,
                    "url": url,
                }
                print("request", url, self.myaccount)
                encoded_protected = self.generate_b64(json.dumps(protected))

                data = f"{encoded_protected}.{payload}".encode("ascii")
                hash = SHA256.new(data)
                signature = self.signer.sign(hash)

                message = {
                    "protected": encoded_protected,
                    "payload": payload,
                    "signature": self.generate_b64(signature),
                }
                header = {"Content-type": "application/jose+json"}
                request = requests.post(
                    url,
                    headers=header,
                    data=json.dumps(message),
                    verify="./pebble.minica.pem",
                )
                print(
                    "execute_dns2",
                    request.status_code,
                    request.content,
                    request.headers,
                )
                self.nonce = request.headers["Replay-Nonce"]
                reqJson = request.json()
                if reqJson["status"] == "valid":
                    break
                sleep(1)

    def execute_http(self, type, record):
        zone = ""
        for domain in self.domains:
            zone += f"{domain}. 60 A {record}" + "\n"
        self.dns = Dns_Server(zone, record)
        self.dns.start_server()
        auth_keys = {}
        for challenge in self.challenges:
            self.challengeUrl.append(challenge["url"])
            authorization_key = self.key_authorization(challenge["token"])
            print("authkey" + authorization_key)
            auth_keys[challenge["token"]] = authorization_key
        print("chalUrl ", self.challengeUrl)
        http_server = hs.http_server(auth_keys)
        http_server.start_http_server(record)

        for challengeUrl in self.challengeUrl:
            payload = {}
            encoded_payload = self.generate_b64(json.dumps(payload))
            protected = {
                "alg": "ES256",
                "nonce": self.nonce,
                "kid": self.myaccount,
                "url": challengeUrl,
            }
            encoded_protected = self.generate_b64(json.dumps(protected))

            data = f"{encoded_protected}.{encoded_payload}".encode("ascii")
            hash = SHA256.new(data)
            signature = self.signer.sign(hash)

            message = {
                "protected": encoded_protected,
                "payload": encoded_payload,
                "signature": self.generate_b64(signature),
            }
            header = {"Content-type": "application/jose+json"}
            request = requests.post(
                challengeUrl,
                headers=header,
                data=json.dumps(message),
                verify="./pebble.minica.pem",
            )
            print(
                "execute_dns",
                request.status_code,
                request.content,
                request.headers,
            )
            self.nonce = request.headers["Replay-Nonce"]
            while True:
                payload = ""
                protected = {
                    "alg": "ES256",
                    "nonce": self.nonce,
                    "kid": self.myaccount,
                    "url": challengeUrl,
                }
                encoded_protected = self.generate_b64(json.dumps(protected))

                data = f"{encoded_protected}.{payload}".encode("ascii")
                hash = SHA256.new(data)
                signature = self.signer.sign(hash)

                message = {
                    "protected": encoded_protected,
                    "payload": payload,
                    "signature": self.generate_b64(signature),
                }
                header = {"Content-type": "application/jose+json"}
                request = requests.post(
                    challengeUrl,
                    headers=header,
                    data=json.dumps(message),
                    verify="./pebble.minica.pem",
                )
                print(
                    "execute_dns2",
                    request.status_code,
                    request.content,
                    request.headers,
                )
                self.nonce = request.headers["Replay-Nonce"]
                reqJson = request.json()
                if reqJson["status"] == "valid":
                    print("juhu")
                    break
                sleep(1)

    def generate_csr(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        csr = (
            x509.CertificateSigningRequestBuilder()
            .subject_name(
                x509.Name(
                    [
                        x509.NameAttribute(NameOID.COUNTRY_NAME, "CH"),
                        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "LU"),
                        x509.NameAttribute(NameOID.LOCALITY_NAME, "Luzern"),
                        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Tschaegge Inc."),
                        x509.NameAttribute(NameOID.COMMON_NAME, "Tschaegge"),
                    ]
                )
            )
            .add_extension(
                x509.SubjectAlternativeName(
                    [x509.DNSName(domain) for domain in self.domains]
                ),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )
        with open("key.pem", "wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        return csr

    def finalization(self):
        csr = self.generate_csr()
        der = csr.public_bytes(serialization.Encoding.DER)
        der = self.generate_b64(der)
        payload = {"csr": der}
        encoded_payload = self.generate_b64(json.dumps(payload))

        protected = {
            "alg": "ES256",
            "kid": self.myaccount,
            "nonce": self.nonce,
            "url": self.finalize,
        }
        encoded_protected = self.generate_b64(json.dumps(protected))
        data = f"{encoded_protected}.{encoded_payload}".encode("ascii")
        hash = SHA256.new(data)
        signature = self.signer.sign(hash)

        message = {
            "protected": encoded_protected,
            "payload": encoded_payload,
            "signature": self.generate_b64(signature),
        }
        header = {"Content-type": "application/jose+json"}
        request = requests.post(
            self.finalize,  # type: ignore
            headers=header,
            data=json.dumps(message),
            verify="./pebble.minica.pem",
        )
        print(
            "finalization",
            request.status_code,
            request.content,
            request.headers,
        )
        self.nonce = request.headers["Replay-Nonce"]

    def download_certificate(self):
        while(True):
            payload = ""
            protected = {
                "alg": "ES256",
                "nonce": self.nonce,
                "kid": self.myaccount,
                "url": self.orderUrl,
            }
            encoded_protected = self.generate_b64(json.dumps(protected))

            data = f"{encoded_protected}.{payload}".encode("ascii")
            hash = SHA256.new(data)
            signature = self.signer.sign(hash)

            message = {
                "protected": encoded_protected,
                "payload": payload,
                "signature": self.generate_b64(signature),
            }
            header = {"Content-type": "application/jose+json"}
            request = requests.post(
                self.orderUrl,  # type: ignore
                headers=header,
                data=json.dumps(message),
                verify="./pebble.minica.pem",
            )
            print(
                "get_cert_url",
                request.status_code,
                request.content,
                request.headers,
            )
            self.nonce = request.headers["Replay-Nonce"]
            reqJson = request.json()
            if reqJson["status"] == "valid":
                self.certificateUrl = reqJson["certificate"]
                break
            sleep(1)

        payload = ""
        protected = {
            "alg": "ES256",
            "nonce": self.nonce,
            "kid": self.myaccount,
            "url": self.certificateUrl,
        }
        encoded_protected = self.generate_b64(json.dumps(protected))

        data = f"{encoded_protected}.{payload}".encode("ascii")
        hash = SHA256.new(data)
        signature = self.signer.sign(hash)

        message = {
            "protected": encoded_protected,
            "payload": payload,
            "signature": self.generate_b64(signature),
        }
        header = {"Content-type": "application/jose+json"}
        request = requests.post(
            self.certificateUrl,  # type: ignore
            headers=header,
            data=json.dumps(message),
            verify="./pebble.minica.pem",
        )
        print(
            "cert",
            request.status_code,
            request.content,
            request.headers,
        )
        self.nonce = request.headers["Replay-Nonce"]
        self.certificate = request.content

        with open("cert.pem", "wb") as f:
            f.write(self.certificate)

    def revoke(self):
        payload = {
            "certificate": self.generate_b64(
                x509.load_pem_x509_certificate(self.certificate).public_bytes( # type: ignore
                    serialization.Encoding.DER
                )
            )
        }
        encoded_payload = self.generate_b64(json.dumps(payload))
        url = self.urls['revokeCert']
        protected = {
            "alg": "ES256",
            "kid": self.myaccount,
            "nonce": self.nonce,
            "url": url,
        }
        encoded_protected = self.generate_b64(json.dumps(protected))
        data = f"{encoded_protected}.{encoded_payload}".encode("ascii")
        hash = SHA256.new(data)
        signature = self.signer.sign(hash)

        message = {
            "protected": encoded_protected,
            "payload": encoded_payload,
            "signature": self.generate_b64(signature),
        }
        header = {"Content-type": "application/jose+json"}
        request = requests.post(
            url,  # type: ignore
            headers=header,
            data=json.dumps(message),
            verify="./pebble.minica.pem",
        )
        print(
            "Revoke",
            request.status_code,
            request.content,
            request.headers,
        )

    def Dns_Test(
        self, record
    ): 
        zone = ""
        for domain in self.domains:
            zone += f"{domain}. 60 A {record}" + "\n"
        self.dns.setZone(zone, record)
