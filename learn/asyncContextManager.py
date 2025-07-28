import asyncio
import time 

class TimerManager:
    async def __aenter__(self):
        self.enter_time = time.time()
        print("Entered the Manager")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        Execution_time = end_time - self.enter_time
        print(f"Time of execution is {Execution_time}")

        if(exc_type):
            print(f"Error occured type :- {exc_type.__name__} : {exc_val}")
            return False

async def main():
    try:
        async with TimerManager():
            print("Task has started...")
            await asyncio.sleep(2)

        
        async with TimerManager():
            print("Task Manager with error has started...")
            await asyncio.sleep(1)

            raise ValueError("Something went wrong")
    except ValueError:
        print(f"Error occur type :- Value Error")

asyncio.run(main())
