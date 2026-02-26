# Importing the necessary libraries
import websockets
import asyncio
import logging
import httpx
import json

logging.basicConfig(level=logging.INFO)

class WebsocketClient:
    def __init__(self, host="localhost", port=8000):
        self.ws_uri = f"ws://{host}:{port}/ws/client123"
        self.api_uri = f"http://{host}:{port}"
        self.websocket = None

    async def sync_password(self, encrypted_package):
        # Send the package to the client with HTTP POST
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api_uri}/sync", json=encrypted_package)
            return response.json()

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.ws_uri)
            logging.info(f"Connected to {self.ws_uri}")
            return True
        except websockets.exceptions.ConnectionClosed:
            logging.warning(f"Connection failed.")
            return False

    async def send(self, data_package: dict):
        if self.websocket:
            await self.websocket.send(json.dumps(data_package))
        else:
            logging.warning("WebSocket connection not estabilished. Cannot send message")

    async def rcv(self):
        try:
            async for msg in self.websocket:
                logging.info(f"Message from server: {msg}")
        except websockets.exceptions.ConnectionClosed:
            logging.warning(f"Connection with server failed.")

    async def run(self):
        if await self.connect():
            receiver_task = asyncio.create_task(self.rcv())
            await self.send({"msg": "New client connected."})
            try:
                await receiver_task
            except asyncio.CancelledError:
                pass
            finally:
                if self.websocket:
                    await self.websocket.close()

if __name__ == "__main__":
    client = WebsocketClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logging.info("Client closed by the user")