import asyncio
import websockets
import json

# This set will store all connected WebSocket clients.
connected_clients = set()

async def register(websocket):
    """Adds a new client to the set of connected clients and sends them their ID."""
    connected_clients.add(websocket)
    # Send the client its own unique ID (its remote address as seen by the server)
    await websocket.send(json.dumps({"type": "your_id", "id": str(websocket.remote_address)}))
    print(f"Client {websocket.remote_address} connected. Total clients: {len(connected_clients)}")

async def unregister(websocket):
    """Removes a client from the set of connected clients."""
    connected_clients.remove(websocket)
    print(f"Client {websocket.remote_address} disconnected. Total clients: {len(connected_clients)}")

async def broadcast(message_data):
    """Sends a structured message (JSON) to all connected clients."""
    if connected_clients:
        # Convert the message_data dictionary to a JSON string
        json_message = json.dumps(message_data)
        await asyncio.gather(*[client.send(json_message) for client in connected_clients])
        print(f"Broadcasted: {json_message}")

async def handler(websocket):
    """
    This is the main handler function for each new WebSocket connection.
    It registers the client, listens for messages, and broadcasts them in JSON format.
    """
    await register(websocket)

    try:
        async for message_text in websocket:
            print(f"Received from {websocket.remote_address}: {message_text}")
            # Prepare the message data to be broadcasted
            message_to_broadcast = {
                "type": "chat_message",
                "sender_id": str(websocket.remote_address), # Identify the sender
                "message": message_text
            }
            await broadcast(message_to_broadcast)
    except websockets.exceptions.ConnectionClosedOK:
        print(f"Client {websocket.remote_address} disconnected gracefully.")
    except Exception as e:
        print(f"An unexpected error occurred with client {websocket.remote_address}: {e}")
    finally:
        await unregister(websocket)

async def main():
    """
    This function starts the WebSocket server.
    It listens on all available interfaces (0.0.0.0) on port 8765.
    """
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("WebSocket chat server started on ws://0.0.0.0:8765")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())