import mysql.connector
import os
from dotenv import load_dotenv

# Initialize the .env to the memory
load_dotenv()

class DBConnector:
    def __init__(self):
        self.config = {
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
        }

    def create_tables_autonomously(self):
        connection = mysql.connector.connect(
            host=self.config["host"],
            user=self.config["user"],
            password=self.config["password"],
        )
        cursor = connection.cursor()
        cursor.execute("CREATE BASE IF NOT EXISTS password_manager")
        cursor.execute("USE password_manager")

        # Create the table of users
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(128)
            password_salt(32)
            )
        """)

        cursor.execute("""CREATE TABLE IF NOT EXISTS credentials (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            service VARCHAR(100),
            login_user VARCHAR(100),
            encrypted_password TEXT,
            iv VARCHAR(32),
            FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)

        connection.commit()
        cursor.close()
        connection.close()