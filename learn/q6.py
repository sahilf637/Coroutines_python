import asyncio

async def long_running_task():
    try:
        for i in range(10):
            print(f"Task {i + 1} executed...")
            await asyncio.sleep(1)
    
    except asyncio.CancelledError:
        print("Task was cancelled")
        raise

async def main():
    task1 = asyncio.create_task(long_running_task())
    await asyncio.sleep(5)

    print("Cancelling the Task now...")
    task1.cancel()

    try:
        await task1
    except asyncio.CancelledError:
        print("Task Cancellation caught in main")

asyncio.run(main())

