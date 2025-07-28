import asyncio
import time

async def fetchData():
    await asyncio.sleep(1)
    print("Data Fetched...")

async def processData():
    await asyncio.sleep(1)
    print("Data Processed...")

async def main():
    start_time = time.perf_counter()
    print("Starting Program...")
    await fetchData()
    await processData()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Execution Time :- {elapsed_time:.4f} second")

asyncio.run(main())