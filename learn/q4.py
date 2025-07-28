import asyncio

async def Task(name, t):
    await asyncio.sleep(t)
    print(f"Task {name} won the race")

async def main():
    print("Starting Task...")
    await asyncio.gather(
        Task("A", 2),
        Task("B", 1),
        Task("C", 3)
    )

asyncio.run(main())