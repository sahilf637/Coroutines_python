import asyncio
import websockets
import sys # For sys.stdin
import json # For parsing JSON messages

# Global variable to store the client's own ID received from the server
my_client_id = None

async def receive_messages(websocket):
    """
    Continuously listens for messages from the WebSocket server,
    parses them, and prints only messages from other users.
    """
    global my_client_id
    try:
        async for message_json in websocket:
            try:
                message_data = json.loads(message_json)

                if message_data.get("type") == "your_id":
                    # This is the special message telling us our own ID
                    my_client_id = message_data.get("id")
                    print(f"Your unique chat ID: {my_client_id}")
                    sys.stdout.write("You: ") # Re-prompt after showing ID
                    sys.stdout.flush()
                elif message_data.get("type") == "chat_message":
                    sender_id = message_data.get("sender_id")
                    message_content = message_data.get("message")

                    # Only print the message if it's from another sender
                    if sender_id != my_client_id:
                        print(f"\n[{sender_id}] {message_content}")
                        sys.stdout.write("You: ") # Re-prompt for user input after receiving a message
                        sys.stdout.flush() # Ensure the prompt is displayed immediately
                    # If it's our own message, we don't print it here
                    # because we've already seen it when we typed it.
            except json.JSONDecodeError:
                print(f"Received malformed JSON: {message_json}")
            except Exception as e:
                print(f"Error processing received message: {e}")
    except websockets.exceptions.ConnectionClosedOK:
        print("Connection closed by the server.")
    except Exception as e:
        print(f"Error receiving message: {e}")

async def send_messages(websocket):
    """
    Continuously prompts the user for input and sends it to the WebSocket server.
    Note: The message is not printed immediately here; it will be displayed
    when received back from the server (if it's from another client).
    """
    try:
        while True:
            sys.stdout.write("You: ") # Prompt for user input
            sys.stdout.flush() # Ensure the prompt is displayed immediately
            message = await asyncio.to_thread(sys.stdin.readline) # Read line from stdin in a non-blocking way
            message = message.strip() # Remove newline character

            if message: # Only send if the message is not empty
                await websocket.send(message)
            await asyncio.sleep(0.1) # Small delay to prevent busy-waiting
    except websockets.exceptions.ConnectionClosedOK:
        print("Connection closed by the server.")
    except Exception as e:
        print(f"Error sending message: {e}")

async def chat_client():
    """
    Connects to the WebSocket server and runs concurrent tasks for sending and receiving messages.
    """
    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to WebSocket chat server at {uri}. Waiting for your ID...")

            # Run sending and receiving tasks concurrently.
            await asyncio.gather(
                receive_messages(websocket),
                send_messages(websocket)
            )
    except ConnectionRefusedError:
        print(f"Connection refused. Is the server running at {uri}?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(chat_client())

