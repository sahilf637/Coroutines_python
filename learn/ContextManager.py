import time

class timerManager:
    def __enter__(self):
        self.start_time = time.time()
        print("Timer has start")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        print(f"Elapsed time is {elapsed_time:.4f} second")

        if exc_type:
            print(f"Exception occur :- {exc_type.__name__} : {exc_val}")
            return False


print("Using Timer Context Manager :-")
with timerManager() as timer:
    print("Inside the context manager work block")
    time.sleep(1.5)
    print("Work Done")


print("Using Timer Context Manager with error")
with timerManager() as timer:
    print("Inside the timer manager with error")
    time.sleep(1)

    raise ValueError("SomeThing went Wrong!")
    print("This line will not be reached")

print("\n code after Error block")