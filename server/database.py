

import mysql.connector
import os

from dotenv import load_dotenv
import uuid
from Client.modules.hash import MasterKey

# Initialize the .env to the memory
load_dotenv()

class DBConnector:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")

    def get_connection(self):
        return mysql.connector.connect(
            host = self.host,
            user = self.user,
            password = self.password,
            database = self.db_name
        )

    def create_tables_autonomously(self):
        connection = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name}")
        cursor.execute(f"USE {self.db_name}")

        # Create the table of users
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(36) UNIQUE NOT NULL,
            user_name VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            password_salt VARCHAR(32) NOT NULL
            )
        """)

        cursor.execute("""CREATE TABLE IF NOT EXISTS credentials (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,   
            service VARCHAR(100) NOT NULL,
            login_user VARCHAR(100),
            encrypted_password TEXT NOT NULL,
            iv VARCHAR(32),
            category VARCHAR(50) DEFAULT 'General',
            FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

class DBSystem(DBConnector):
    def __init__(self):
        super().__init__()

    # Register the new user and save its information
    def register_user(self, user_name, password_hash, salt):
        connection = self.get_connection()
        cursor = connection.cursor()
        user_id = str(uuid.uuid4())
        data = "INSERT INTO users (user_name, password_hash, password_salt, user_id) VALUES (%s, %s, %s, %s)"
        query = "SELECT user_name FROM users WHERE username = %s"

        try:
            # Verifiy the user_name
            cursor.execute(query, (user_name,))
            if cursor.fetchone():
                return False # Return False if the user_name is in database

            # Insert a new user
            cursor.execute(data, (user_name, password_hash, salt, user_id))
            connection.commit()
            return True

        except Exception as e:
            print(f"Error: {e}")
            return False

        finally:
            cursor.close()
            connection.close()

    # Function for verifying the user and password when in login
    def login_user(self, user_name, password):
        connection = self.get_connection()
        cursor = connection.cursor()

        query = "SELECT id, password_hash, password_salt FROM users WHERE user_name = %s"
        cursor.execute(query, (user_name,))
        result = cursor.fetchone()

        if result:
            user_db_id, stored_hash, salt = result

            master_key = MasterKey(input_password=password)

            if master_key.verify_masterkey(stored_hash, salt):
                return user_db_id

        return None

    # Function for registering a password in database
    def registering_password(self, user_id, service, login_user, encrypted_password, iv_hex, category):
        connection = self.get_connection()
        cursor = connection.cursor()

        try:
            data = "INSERT INTO credentials (user_id, service, login_user, encrypted_password, iv, category) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(data, (user_id, service, login_user, encrypted_password, iv_hex, category))
            connection.commit()
            return True
        except Exception as e:
            print(f"SQL Error: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

    # Rewrite existing data
    def rewrite_data(self, service, login_user, encrypted_password, iv_hex, credential_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        try:
            query = "UPDATE credentials (service, login_user, encrypted_password, iv) VALUES (%s, %s, %s, %s) WHERE id = %s"
            cursor.execute(query, (service, login_user, encrypted_password, iv_hex, credential_id))
            connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

    # Delete a registered password
    def delete_password(self, credential_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        try:
            query = "DELETE FROM credentials WHERE id = %s"
            cursor.execute(query, (credential_id,))
            connection.commit()
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

    # Make a request and post the data
    def get_user_passwords(self, user_id, category):
        connection = self.get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            query = "SELECT id, service, login_user, encrypted_password, iv FROM credentials WHERE user_id = %s AND category = %s"
            cursor.execute(query, (user_id, category))

            return cursor.fetchall()

        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

    def get_categories(self, user_id):
        connection = self.get_connection()
        cursor = connection.cursor()

        try:
            query = "SELECT DISTINCT category FROM credentials WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cursor.close()
            connection.close()