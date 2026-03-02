# Password Manager
This project is made using pure Python and utilizes hybrd encryption for safety management and with the purpose of study and auto improvement.
## Tecnlogies
* **Language:** Python
* **GUI:** PySide6 (Qt for Python)
* **Backend:** FastAPI (Asynchronous Middleware)
* **Database:** MySQL
* **Communication:** HTTP Requests & WebSockets
* **Security:** Cryptography (AES-256 GCM, RSA-4096, SHA3-512, PBKDF2)

## Architecture explanation
- **Middleware API:** A FastAPI server acts as a bridge between the Client and the Database. The Client never communicates directly with MySQL.
- **Autonomous Database:** The system automatically creates the MySQL database and the required tables upon the first run of the middleware.
- **User Authentication:** Master keys are stored using **SHA3-512** with a unique salt per user.
- **Key Derivation:** The AES-256 key used for local encryption is derived from the Master Key using **PBKDF2-HMAC-SHA512** (100k iterations).
- **Hybrid Cryptography:** All data transport between Client and Middleware is protected by a hybrid system:
    1. Data is encrypted with a random **Session AES Key**.
    2. The Session Key is then encrypted using the **Server's RSA Public Key**.
- **Client-Side Decryption:** Passwords are only decrypted on the user's machine, ensuring the server never sees the raw data.

## How to install
Clone the repository
### 1. Clone the repository
```bash
git clone [https://github.com/Kenshin1072/PasswordManager.git](https://github.com/Kenshin1072/PasswordManager.git)
cd PasswordManager
``` 
### 2. Create the virtual environment
``` bash
python -m venv .venv
``` 
### 3. Install the requirements for the code
```  bash
pip install -r requirements.txt
``` 
### 4. Create an archive named .env and put your credentials from MySQL
``` bash
DB_HOST=localhost
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=password_manager
``` 
### 5. Execute the middleware for the program to create the tables
``` bash
python server/middleware.py
``` 
### 6. Open the client
``` bash
python client/main.py
``` 

## Libraries
### Security
- **cryptography**: This library is a gold standard for Python. It handles AES-256 and RSA.
- **hashlib**: It comes built-in with Python and has SHA3-512 for the Master Key storage.
### Communication & Backend
- **FastAPI &  uvicorn**: These are used in place of the RestAPI because are for Python and are extremely modern and fast, making it easy for the Middleware.
- **requests & httpx**: Are messengers required for the client and http.
- **websockets**: This was prefered for to facilitate the connection in real time and for study purpose.
### GUI
- **PySide**: This is a modern GUI interface for Python and was chosen because of indication.