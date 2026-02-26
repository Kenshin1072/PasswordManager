import hashlib
import os

# Class for master key using SHA3-512 + salt
class MasterKey(object):
    def __init__(self, input_password):
        self.input_password = input_password

    @staticmethod
    def hash_masterkey(key: str):
        # Generate an aleatory salt
        salt = os.urandom(16)
        return hashlib.sha3_512(key.encode() + salt).hexdigest(), salt.hex()

    def verify_masterkey(self, stored_hash, stored_salt_hex):
        salt = bytes.fromhex(stored_salt_hex)
        return hashlib.sha3_512(self.input_password.encode() + salt).hexdigest() == stored_hash