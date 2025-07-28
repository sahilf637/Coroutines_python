import asyncio
import time

async def fetch_data():
    await asyncio.sleep(1)
    print("Data is Fetched...")

async def process_data():
    print("Processing start")
    await asyncio.sleep(1)
    print("Data is Processed...")

async def main():
    task1 = asyncio.create_task(fetch_data())
    task2 = asyncio.create_task(process_data())
    print("Starting processing")
    start_time = time.perf_counter()
    await task1
    await task2
    end_time = time.perf_counter()
    processing_time = end_time - start_time
    print(f"Exectution time :- {processing_time:.4f} seconds")

asyncio.run(main())

