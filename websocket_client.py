# Importing the necessary libraries
import websockets
import asyncio
import logging

from pydantic.v1.networks import host_regex

logging.basicConfig(level=logging.INFO)

class WebsocketClient:
    def __init__(self, host="localhost", port=8000):
        self.uri = f"ws://{host}:{port}"
        self.websocket = None

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            logging.info(f"Connected to {self.uri}")
            return True
        except websockets.exceptions.ConnectionClosed as e:
            logging.warning(f"Connection failed.")
            return False

    async def send(self, msg):
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.send(msg)
            except Exception as e:
                logging.error(e)
        else:
            logging.warning("WebSocket connection not estabilished. Cannot send message")

    async def rcv(self):
        if self.websocket and not self.websocket.closed:
            try:
                async for msg in self.websocket:
                    logging.info(msg)
            except websockets.exceptions.ConnectionClosed as e:
                logging.warning(f"Connection failed.")
            except Exception as e:
                logging.error(f"Connection failed; {e}")

    async def run(self):
        await self.connect()

        receiver_task = asyncio.create_task(self.rcv())
        await self.send({"msg": "New client connected."})
        await receiver_task

if __name__ == "__main__":
    client = WebsocketClient()
    asyncio.run(client.run())