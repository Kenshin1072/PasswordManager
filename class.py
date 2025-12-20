import platform
import threading
import socket
import random
from cryptography.fernet import Fernet
class PasswordManager:
    def __init__(self, password):
        self._key = None
        self._password_file = None
        self._password_dict = {}

    def create_key(self, path):
        self._key = Fernet.generate_key()
        with open(path, 'wb') as file:
            file.write(self._key)

    def load_key(self, path):
        with open(path, 'rb') as file:
            self._key = file.read()

    def create_password_file(self, path, initial_values=None):
        self._password_file = path

        if initial_values is not None:
            for key, values in initial_values.items():
                self._password_dict[key] = values

    def load_passsword_file(self, path):
        self._password_file = path

        with open(path, 'r') as file:
            for line in file:
                site, encrypted = line.strip().split(':')
                self._password_dict[site] = Fernet(self._key).decrypt(encrypted.encode()).decode()

    def add_password(self, site, password):
        self._password_dict[site] = password

        if self._password_file is not None:
            with open(self._password_file, 'a') as file:
                encrypted = Fernet(self._key).encrypt(password.encode()).decode()

class Password(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
class Server(threading.Thread):
    def __init__(self, hostname, port):
        threading.Thread.__init__(self)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((hostname, port))
    def connect(self):
        while True:
            connection, address = self._socket.accept()
            self._connections.append(connection)
    def get_hostname(self): return self.get_hostname()
    def get_port(self): return self.get_port()

class Peer(threading.Thread):
    SERVER_HOST_NAME = platform.node()
    def __init__(self, hostname, port):
        self._hostname = hostname
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connections = []
        threading.Thread.__init__(self)
