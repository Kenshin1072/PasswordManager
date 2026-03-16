import os
from collections import defaultdict
import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import json
from Client.modules.encryption import AESSystem, RSASystem
from server.database import DBSystem
from typing import Dict
from contextlib import asynccontextmanager

# API logic

class MiddlewareAPI:
    def __init__(self):
        # Generate its RSA KEY when initializing
        self.rsa = RSASystem()
        self.db = DBSystem()
    def decrypt_package(self, encrypted_session_key_hex, encrypted_payload_hex):
        # Retrieve the sessions key
        session_key_hex = self.rsa.rsa_decryption(encrypted_session_key_hex)

        # Uses the key to openthe AES data
        aes_handler = AESSystem(key_hex=session_key_hex)
        original_data = aes_handler.aes_decryption_with_embedded_iv(encrypted_payload_hex)

        return original_data

middleware_logic = MiddlewareAPI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    middleware_logic.db.create_tables_autonomously()
    print("Middleware startup")
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)

class Middleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit_records: Dict[str, float] = defaultdict(float)

    async def dispatch(self, request: Request, call_next):
        client_ip = "127.0.0.1"
        if request.client:
            client_ip = request.client.host

        if request.method == "POST":
            current_time = time.time()
            last_request_time = self.rate_limit_records.get(client_ip, 0)

            if current_time - last_request_time < 0.1:
                return Response(content=json.dumps({"error": "Rate limit reached"}), status_code=429, media_type="application/json")

            self.rate_limit_records[client_ip] = current_time
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response

app.add_middleware(Middleware)

@app.get("/public-key")
async def get_public_key():
    public_key_pem = middleware_logic.rsa.get_public_key()
    return {"public_key": public_key_pem}

@app.get("/get-categories/{user_id}")
async def get_categories(user_id: str):
    categories = middleware_logic.db.get_categories(user_id)
    return {"categories": categories}

@app.get("/get-passwords/{user_id}/{category}")
async def get_passwords(user_id: str, category: str):
    passwords = middleware_logic.db.get_user_passwords(user_id, category)
    return {"passwords": passwords}

@app.post("/sync")
async def rcv_data(request: Request):
    try:
        #receives the package from Client
        data = await request.json()

        decrypted_data = middleware_logic.decrypt_package(
            data["session_key"], data["payload"])

        # Transform into a dict
        credential = json.loads(decrypted_data)

        # Saves in the MySQL database
        success = middleware_logic.db.registering_password(
            user_id=credential["user_id"],
            service=credential["service"],
            login_user=credential["login_user"],
            encrypted_password=credential["encrypted_content"],
            iv_hex=credential["iv"],
            category=credential.get("category", "General")
        )

        if not success:
            raise Exception("Database failed to save. Check if user_id exist in 'users' table." )

        return {"status": "success", "message": "Data is in database"}

    except Exception as e:
        print(f"Error when receiving data, error; {e}")
        raise HTTPException(status_code=400, detail=str(e))



if __name__ == "__main__":
    host = os.getenv("API_HOST", "localhost")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host=host, port=port)