from PySide6.QtWidgets import  QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel



class AddPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Password Screen")
        layout = QVBoxLayout(self)

        # Title line for identify purposes
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Service (ex: Facebook, Bank...")

        # User login
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Email or Username")

        # Password line with hiding system
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        btn_save = QPushButton("Save Password")
        btn_save.clicked.connect(lambda: self.accept())

        layout.addWidget(QLabel("Identification title:"))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("User/Login"))
        layout.addWidget(self.user_input)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)
        layout.addWidget(btn_save)

    def get_data(self):
        return self.title_input.text(), self.user_input.text(), self.password_input.text()