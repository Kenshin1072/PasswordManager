import sys
from PySide6.QtWidgets import QApplication
from Client.ui.main_screen import MainWindow

def main():
    # Initializing the app
    app = QApplication(sys.argv)

    # Login simulation for test only
    test_user_id = "user-test-123"
    test_master_key = b'1234567890123456'

    window = MainWindow(user_id=test_user_id, master_key=test_master_key)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()