import json
import secrets

from cryptography.hazmat.backends import default_backend
from  cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class AESSystem:
    def __init__(self, key_hex=None):
        if key_hex:
            self.key = bytes.fromhex(key_hex)
        else:
            self.key = AESGCM.generate_key(bit_length=256)

    # Symetric encryption in AES-256
    def aes_encryption(self, password: str):
        aes = AESGCM(self.key)
        nonce = secrets.token_bytes(12)

        # cryptography
        ciphertext = aes.encrypt(nonce, password.encode(), None)

        return ciphertext.hex(), nonce.hex()

    # Receives the key and the encrypted password to decrypt
    def aes_decryption(self, encrypted_hex: str, iv_hex: str):
        aes = AESGCM(self.key)
        ciphertext = bytes.fromhex(encrypted_hex)
        nonce = bytes.fromhex(iv_hex)

        plaintext = aes.decrypt(nonce, ciphertext, None)

        return plaintext.decode() # return the original string

    def aes_decryption_with_embedded_iv(self, combined_hex: str):
        data = bytes.fromhex(combined_hex)
        nonce = data[:12]
        ciphertext = data[12:]

        aes = AESGCM(self.key)
        plaintext = aes.decrypt(nonce, ciphertext, None)
        return plaintext.decode()

class RSASystem:
    def __init__(self, private_key=None):
        if private_key is None:
            self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
        else:
            self.private_key = private_key

        self.public_key = self.private_key.public_key()

    # Symetric encryption
    @staticmethod
    def rsa_encryption(plaintext: str, public_key_object):
        # Uses the public key to encrypt
        ciphertext = public_key_object.encrypt(
            plaintext.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA512()),
                algorithm=hashes.SHA512(),
                label=None,
            )
        )
        return ciphertext.hex()

    def rsa_decryption(self, ciphertext_hex: str):
        # Middleware uses the private key to decrypt
        ciphertext = bytes.fromhex(ciphertext_hex)
        plaintext = self.private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA512()),
                algorithm=hashes.SHA512(),
                label=None,
            )
        )
        return plaintext.decode()

    def load_private_key(self):
        with open("private_key.pem", "rb") as key_file:
            self.private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )

    def get_public_key(self):
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode("utf-8")


class KeyDerivator:
    @staticmethod
    def derive_aes_key(master_password: str, salt_hex: str):
        # Transform the salt hex to bytes
        salt = bytes.fromhex(salt_hex)

        # PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA512(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        key = kdf.derive(master_password.encode())
        return key.hex()

class HybridManager:
    def __init__(self):
        self.rsa = RSASystem()
        self.session_aes = AESSystem()

    def prepare_for_middleware(self, data_str: str, server_public_key):
        pub_key_obj = serialization.load_pem_public_key(server_public_key.encode(), backend=default_backend())

        # Create a temporary random key
        session_aes_hex = self.session_aes.key.hex()

        # Encrypt the data with the session key
        ct_hex, iv_hex = self.session_aes.aes_encryption(data_str)
        combined_payload = iv_hex + ct_hex

        # Encrypt the session key with the public key RSA of the middleware
        encrypted_session_key = self.rsa.rsa_encryption(session_aes_hex, pub_key_obj)

        # Create the JSON package for HTTP
        package = {
            "session_key": encrypted_session_key,
            "payload": combined_payload,
        }
        return package

    def decrypt_package(self, package_json: str):
        package = json.loads(package_json)

        # Retrieve the sessions key
        session_key_hex = self.rsa.rsa_decryption(package["session_key"])

        # Uses the key to open the AES data
        session_aes = AESSystem(key_hex=session_key_hex)
        original_data = session_aes.aes_decryption_with_embedded_iv(package["payload"])

        return original_data