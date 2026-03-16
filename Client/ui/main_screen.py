import json

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QStackedWidget, QPushButton, \
    QScrollArea, QGridLayout, QInputDialog, QMessageBox

import requests

from Client.modules.encryption import AESSystem, HybridManager


from Client.ui.add_password_screen import AddPasswordDialog

import os
from dotenv import load_dotenv

load_dotenv()
SERVER_URL = os.getenv("SERVER_HOST", "https://127.0.0.1:8000")

class MainWindow(QMainWindow):
    def __init__(self, user_id, master_key):
        super().__init__()
        self.hybrid_manager = HybridManager()
        self.master_key = master_key
        self.user_id = user_id
        self.server_public_key = self.fetch_server_key()

        self.setWindowTitle("Password Manager")
        self.resize(600, 500)

        # Stack the windows ( Principal container )
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.btn_back = None
        self.current_folder_id = None

        # Home widget
        self.home_widget = QWidget()
        self.home_layout = QVBoxLayout(self.home_widget)

        # Scrolling system for folders or passwords
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.scroll.setWidget(self.container)

        self.home_layout.addWidget(self.scroll)

        # Principal action button
        self.btn_action = QPushButton("Create new repository")
        self.btn_action.clicked.connect(self.handle_main_action)
        self.home_layout.addWidget(self.btn_action)

        self.stack.addWidget(self.home_widget)
        self.refresh_view()

    # A button that create a folder if the user is not in a folder, else creates a new credential to add
    def handle_main_action(self):
        if self.current_folder_id is None:
            self.create_new_folder()
        else:
            self.add_new_password()

    @staticmethod
    def fetch_server_key():
        try:
            resp = requests.get(f"{SERVER_URL}/public-key")
            if resp.status_code == 200:
                data = resp.json()
                if "public_key" in data:
                    return resp.json()["public_key"]
                else:
                    print("JSON does not has 'public_key")
            else:
                print(f"Server error ({resp.status_code}): {resp.text}")
            return None
        except Exception as e:
            print(f"Error trying to search server key: {e}")
            return None

    def create_new_folder(self):
        name, ok = QInputDialog.getText(self, "New Repository", "Name of Repository:")
        if ok and name:
            self.enter_folder(name)

    def add_new_password(self):
        dialog = AddPasswordDialog(self)
        if dialog.exec():
            service, user_login, password = dialog.get_data()
            self.process_new_password(service, user_login, password)

    def process_new_password(self, service, login, password):
        try:
            if self.server_public_key is None:
                self.server_public_key = self.fetch_server_key()


            aes_internal = AESSystem(key_hex=self.master_key.hex())
            encrypted_pw, iv_pw = aes_internal.aes_encryption(password)

            # Prepare for the Middleware
            payload = {
                "user_id": self.user_id,
                "service": service,
                "login_user": login,
                "encrypted_content": encrypted_pw,
                "iv": iv_pw,
                "category": self.current_folder_id
            }

            package = self.hybrid_manager.prepare_for_middleware(data_str=json.dumps(payload), server_public_key=self.server_public_key)
            response = requests.post(f"{SERVER_URL}/sync", json=package)

            if response.status_code == 200:
                QMessageBox.information(self, "Success", f"Password for: {service} sent.")
                self.current_folder_id = None
                self.refresh_view()
            else:
                print(f"Server error: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process: {e}")

    def enter_folder(self, folder_name):
        self.current_folder_id = folder_name
        if not self.btn_back:
            self.btn_back = QPushButton("Back")
            self.btn_back.clicked.connect(self.go_back)
            self.home_layout.insertWidget(0, self.btn_back)
        self.refresh_view()

    def go_back(self):
        self.current_folder_id = None
        if self.btn_back:
            self.btn_back.deleteLater()
            self.btn_back = None
        self.refresh_view()

    def refresh_view(self):
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        if self.current_folder_id is None:
            self.btn_action.setText("Create New Repository")
            self.load_folders_from_db()
        else:
            self.btn_action.setText("New Password")
            self.load_passwords_from_db()

    def load_folders_from_db(self):
        try:
            categories = []

            url = f"{SERVER_URL}/get-categories/{self.user_id}"
            response = requests.get(url)

            if response.status_code == 200:
                categories = response.json().get("categories", [])

            row, col = 0, 0
            for name in categories:
                btn = QPushButton(name)
                btn.setFixedSize(120, 100)
                btn.setStyleSheet("font-weight: bold; background-color: #f0f0f0;")

                btn.clicked.connect(lambda ch=False, n=name: self.enter_folder(n))
                self.grid_layout.addWidget(btn, row, col)
                col += 1
                if col > 3:
                    col = 0
                    row += 1
        except Exception as e:
            print(f"Error when loading folders: {e}")

    def load_passwords_from_db(self):
        try:
            url = f"{SERVER_URL}/get-passwords/{self.user_id}/{self.current_folder_id}"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                passwords_list = data["passwords"]

                for i, cred in enumerate(passwords_list):

                    btn = QPushButton(f"{cred['service']}")
                    btn.setFixedSize(120, 100)

                    btn.clicked.connect(lambda ch=False, c=cred: self.reveal_password(c))

                    self.grid_layout.addWidget(btn, i //3, i % 3)

            else:
                print("Error when searching for data")

        except Exception as e:
            print(f"Failed to connect: {e}")

    def reveal_password(self, credential_dict):
        try:
            from Client.modules.encryption import AESSystem
            encrypted_pw = credential_dict['encrypted_password']
            iv_hex = credential_dict['iv']
            service_name = credential_dict['service']

            master_key_hex = self.master_key.hex() if isinstance(self.master_key, bytes) else self.master_key

            cipher = AESSystem(key_hex=master_key_hex)
            fully_encrypted_data = iv_hex + encrypted_pw
            decrypted_password = cipher.aes_decryption(encrypted_pw, iv_hex)

            QMessageBox.information(self, "Password revelead",
                                    f"service: {service_name}\n"
                                    f"Users: {credential_dict['login_user']}\n"
                                    f"Password: {decrypted_password}",)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"The master key can't open this password\n Error: {e}")
