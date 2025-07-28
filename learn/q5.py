import asyncio
import random

queue = []
cnt = 1
async def Producer():
    global cnt
    while True:
        queue.append(f"Task {cnt}")
        cnt += 1
        await asyncio.sleep(random.random())

async def Consumer():
    while True:
        while len(queue) == 0:
            await asyncio.sleep(random.random())
        
        tk = queue.pop()
        await asyncio.sleep(random.random())
        print(f"Consumer Completed {tk}")

async def main():
    Producer_task1 = asyncio.create_task(Producer())
    Producer_task2 = asyncio.create_task(Producer())
    Consumer_task1 = asyncio.create_task(Consumer())
    Consumer_task2 = asyncio.create_task(Consumer())
    Consumer_task3 = asyncio.create_task(Consumer())

    print("Starting Simulation...")
    await asyncio.gather(Producer_task1, Producer_task2, Consumer_task1, Consumer_task2, Consumer_task3)

asyncio.run(main())