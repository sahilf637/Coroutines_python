import asyncio

clients = set()

async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"Connected by {addr}")
    clients.add(writer)

    try:
        while data := await reader.readline():
            message = data.decode().strip()
            print(f"{addr}: {message}")

            for client in clients:
                if client != writer:
                    client.write(f"{addr}: {message}\n".encode())
                    await client.drain()
    except (asyncio.CancelledError, ConnectionResetError):
        pass
    finally:
        print(f"{addr} disconnect.")
        clients.remove(writer)
        writer.close()
        await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, "localhost", 8888)
    print("Chat server started on localhost:8888")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())