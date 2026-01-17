import hashlib
import os

# Classe para a chave mestra usando SHA3-512 + salt
class MasterKey(object):
    def __init__(self, key: str, stored_salt_hex, stored_hex, input_password):
        self.key = key
        self.stored_salt_hex = stored_salt_hex
        self.stored_has = stored_hex
        self.input_password = input_password

    def hash_masterkey(self):
        # Gerando um salt aleatório
        salt = os.urandom(16)
        return hashlib.sha3_512(self.key.encode() + salt).hexdigest(), salt.hex()

    def verify_masterkey(self):
        salt = bytes.fromhex(self.stored_salt_hex)
        return hashlib.sha3_512(self.input_password.encode() + salt).hexdigest() == self.stored_hex