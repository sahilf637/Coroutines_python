import asyncio

async def send_messages(writer):
    while True:
        msg = await asyncio.get_event_loop().run_in_executor(None, input)
        writer.write(f"{msg}\n".encode())
        await writer.drain()

async def receive_messages(reader):
    while True:
        data = await reader.readline()
        if not data:
            break
        print(data.decode().strip())

async def main():
    reader, writer = await asyncio.open_connection("localhost", 8888)
    print("Connected to chat!")

    await asyncio.gather(
        send_messages(writer),
        receive_messages(reader)
    )

if __name__ == "__main__":
    asyncio.run(main())
