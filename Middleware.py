from collections import defaultdict
from typing import Dict
from urllib import response

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
import json
from modules.encryption import RSA, AES
from database import DBConnector

app = FastAPI()

class Middleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit_records = defaultdict(float)

    async def dispatch(self, request: Request, call_next, response_headers=None):
        client_ip = request.client.host
        current_time = time.time()

        if current_time - self.rate_limit_records[client_ip] < 1:
            return Response(content="Rate limit reached", status_code=429)

        self.rate_limit_records[client_ip] = current_time
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response_headers["X-Process-Time"] = str(process_time)
        return response

app.add_middleware(Middleware)

# API logic

class MiddlewareAPI:
    def __init__(self):
        # Generate its RSA KEY when initializing
        self.rsa = RSA()
        self.db = DBConnector()
    def decrypt_package(self, encrypted_session_key_hex, encrypted_payload_hex):
        # Retrieve the sessions key
        session_key_hex = self.rsa.rsa_decryption(encrypted_session_key_hex)

        # Uses the key to openthe AES data
        aes_handler = AES(key_hex=session_key_hex)
        original_data = aes_handler.aes_decryption(encrypted_payload_hex)

        return original_data

middleware_logic = MiddlewareAPI()

# Endpoints

@app.on_event("startup")
async def startup():
    middleware_logic.db.create_tables_autonomously()
    print("Middleware startup")

@app.get("/public-key")
async def get_public_key():
    return {"public_key": middleware_logic.db.get_public_key()}

@app.post("/sync")
async def rcv_data(request: Request):
    try:
        #receives the package from Client
        data = await request.json()

        decrypted_data = middleware_logic.decrypt_package(
            data["session_key_hex"], data["payload_hex"
        ])

        # Transform into a dict
        credential = json.loads(decrypted_data)

        # Saves in the MySQL database
        middleware_logic.db.save_credentials(
            user_id=credential["user_id"],
            service=credential["service"],
            encrypted_data=credential["encrypted_data"],
            iv=credential["iv"],
        )

        return {"status": "success", "message": "Data is in database"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)