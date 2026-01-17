# importing the necessary libraries
import asyncio
import logging
import websockets
import uuid
import websockets.exceptions

# Configure Logging for better visibility
logging.basicConfig(level=logging.INFO)

# Defining the server data
PORT = 8000

class Server:
    def __init__(self, port=PORT):
        self.host = "localhost"
        self.port = port
        self.connection_clients = set()

    async def handle_connection(self, websocket):
        # Registers the client
        self.clients.add(websocket)
        client_id = str(uuid.uuid4())
        logging.info(f"Client {client_id} connected")

        try:
            # Sends the ID for the client
            await websocket.send(f"ID assigned {client_id}")

            async for msg in websocket:
                logging.info(msg)
                for client in self.clients:
                    if client != websocket:
                        await client.send(msg)
        except websockets.exceptions.ConnectionClosed as e:
            logging.error(f"{e} br {websocket.remote_address}")
        finally:
            self.clients.remove(websocket)

    async def run(self):
        logging.info(f"Server started at ws://{self.host}:{self.port}")
        async with websockets.serve(self.handle_connection, self.host, PORT):
            await asyncio.Future()

if __name__ == "__main__":
    server = Server()
    asyncio.run(server.run())
