import asyncio

async def say_hello():
    await asyncio.sleep(0)
    print("Hello...")

async def task():
    print("Step 1")
    await asyncio.sleep(0)  # Yield control to the event loop
    print("Step 2")

async def main():
    await task()
    task1 = asyncio.create_task(say_hello())
    task2 = asyncio.create_task(task())

    print("Printing start")
    await task1
    await task2

asyncio.run(main())
