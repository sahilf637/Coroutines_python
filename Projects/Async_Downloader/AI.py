import asyncio
import aiofiles
import aiohttp
from tqdm.asyncio import tqdm
import sys
import os

class DownloadManager:
    def __init__(self):
        self.downloads = {}  # {filename: {'url': url, 'task': task, 'event': event, 'status': 'pending'/'downloading'/'paused'/'completed'/'failed'}}
        self.active_downloads_limit = 3 # Limit concurrent downloads (adjust as needed)
        self.active_downloads_count = 0
        self.queue = asyncio.Queue() # To manage downloads when limit is active
        self.stop_event = asyncio.Event() # To signal the main loop to stop

    async def _worker(self):
        """Worker to process downloads from the queue."""
        while not self.stop_event.is_set():
            try:
                filename = await asyncio.wait_for(self.queue.get(), timeout=1.0) # Small timeout to check stop_event
            except asyncio.TimeoutError:
                continue # No items in queue, check stop_event again

            if self.stop_event.is_set():
                break # Exit if stop signal received

            dl_info = self.downloads[filename]
            url = dl_info['url']
            event = dl_info['event']

            self.active_downloads_count += 1
            dl_info['status'] = 'downloading'
            print(f"\n[Manager] Starting download: {filename}")

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            size = int(response.content_length)
                            async with aiofiles.open(filename, "wb") as fs:
                                with tqdm(total=size, unit='B', unit_scale=True, desc=f"Downloading {filename}") as progress_bar:
                                    while True:
                                        await event.wait() # Await the individual download's event
                                        chunk = await response.content.read(1024*1024)
                                        if not chunk:
                                            break
                                        await fs.write(chunk)
                                        progress_bar.update(len(chunk))
                            print(f"\n[Manager] Downloaded file: {filename}")
                            dl_info['status'] = 'completed'
                        else:
                            print(f"\n[Manager] Failed to download {url} (HTTP {response.status}) for {filename}")
                            dl_info['status'] = 'failed'
            except aiohttp.client_exceptions.ServerDisconnectedError:
                print(f"\n[Manager] Server disconnected while downloading {filename}. Retrying or handling error.")
                dl_info['status'] = 'failed' # Or implement retry logic
            except aiohttp.ClientConnectionError:
                print(f"\n[Manager] Connection error while downloading {filename}. Retrying or handling error.")
                dl_info['status'] = 'failed' # Or implement retry logic
            except Exception as e:
                print(f"\n[Manager] An unexpected error occurred during download of {filename}: {e}")
                dl_info['status'] = 'failed'
            finally:
                self.active_downloads_count -= 1
                self.queue.task_done() # Mark task as done in the queue

    async def add_download(self, filename, url):
        if filename in self.downloads:
            print(f"Error: Download '{filename}' already exists.")
            return

        event = asyncio.Event()
        event.set() # Downloads start unpaused by default
        self.downloads[filename] = {
            'url': url,
            'task': None, # Worker will handle the task, no need to store here initially
            'event': event,
            'status': 'pending'
        }
        await self.queue.put(filename)
        print(f"Added '{filename}' to download queue.")

    def pause_download(self, filename):
        if filename not in self.downloads:
            print(f"Error: Download '{filename}' not found.")
            return
        if self.downloads[filename]['status'] == 'completed':
            print(f"Download '{filename}' is already completed.")
            return
        
        self.downloads[filename]['event'].clear()
        self.downloads[filename]['status'] = 'paused'
        print(f"Paused download: {filename}")

    def resume_download(self, filename):
        if filename not in self.downloads:
            print(f"Error: Download '{filename}' not found.")
            return
        if self.downloads[filename]['status'] == 'completed':
            print(f"Download '{filename}' is already completed.")
            return

        self.downloads[filename]['event'].set()
        self.downloads[filename]['status'] = 'downloading' # Assuming it will resume downloading
        print(f"Resumed download: {filename}")

    def get_status(self):
        if not self.downloads:
            print("No downloads in progress.")
            return
        print("\n--- Download Status ---")
        for filename, info in self.downloads.items():
            print(f"  {filename}: {info['status']} (URL: {info['url']})")
        print("-----------------------\n")

    async def start(self):
        # Start worker tasks
        self.worker_tasks = [asyncio.create_task(self._worker()) for _ in range(self.active_downloads_limit)]
        # Initial downloads can be added here, or via user command later
        
        # Keep the manager running until explicitly told to stop
        await self.stop_event.wait() 
        
        # Signal workers to stop
        for _ in self.worker_tasks:
            self.stop_event.set() # Set for each worker
        await asyncio.gather(*self.worker_tasks) # Wait for workers to finish
        print("Download manager stopped.")


async def take_command(manager: DownloadManager):
    print("Welcome to the Async Download Manager!")
    print("Commands: add <filename> <url>, pause <filename>, resume <filename>, status, stop")
    while not manager.stop_event.is_set():
        sys.stdout.write("Enter command > ")
        sys.stdout.flush()
        command_line = await asyncio.to_thread(sys.stdin.readline)
        command_line = command_line.strip()
        parts = command_line.split()

        if not parts:
            continue

        command = parts[0].lower()

        if command == "add":
            if len(parts) == 3:
                filename = parts[1]
                url = parts[2]
                await manager.add_download(filename, url)
            else:
                print("Usage: add <filename> <url>")
        elif command == "pause":
            if len(parts) == 2:
                filename = parts[1]
                manager.pause_download(filename)
            else:
                print("Usage: pause <filename>")
        elif command == "resume":
            if len(parts) == 2:
                filename = parts[1]
                manager.resume_download(filename)
            else:
                print("Usage: resume <filename>")
        elif command == "status":
            manager.get_status()
        elif command == "stop":
            print("Stopping download manager...")
            manager.stop_event.set() # Signal manager to stop
            break
        else:
            print("Unknown command. Type 'help' for options.")

async def main():
    manager = DownloadManager()

    # Add some initial files to download
    await manager.add_download("test1.bin", "https://ash-speed.hetzner.com/100MB.bin")
    await manager.add_download("test2.bin", "https://fsn1-speed.hetzner.com/100MB.bin")
    await manager.add_download("test3.bin", "https://fsn1-speed.hetzner.com/1GB.bin")
    await manager.add_download("test4.bin", "https://fsn1-speed.hetzner.com/50MB.bin")


    # Start the command listener and the download manager
    command_task = asyncio.create_task(take_command(manager))
    manager_task = asyncio.create_task(manager.start())

    # Wait for both to complete (manager will complete when stop_event is set)
    await asyncio.gather(command_task, manager_task)
    print("All tasks finished.")

if __name__ == "__main__":
    # Clean up previous downloads if they exist for testing
    for f in ["test1.bin", "test2.bin", "test3.bin", "test4.bin"]:
        if os.path.exists(f):
            os.remove(f)
            print(f"Removed old {f}")

    asyncio.run(main())