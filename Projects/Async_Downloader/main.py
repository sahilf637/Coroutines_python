import asyncio
import aiofiles
import aiohttp
from tqdm.asyncio import tqdm
import sys

async def download(url, filename, event):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    size = int(response.content_length)
                    async with aiofiles.open(filename, "wb") as fs:
                        with tqdm(total=size, unit='B', unit_scale=True, desc=f"Downloading {filename}") as progress_bar:
                            while True:
                                await event.wait()
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                await fs.write(chunk)
                                progress_bar.update(len(chunk))
                    
                    print(f"Downloaded file {filename}")
                else:
                    print(f"Failed to download {url} : {response.status}")
    
    except aiohttp.client_exceptions.ServerDisconnectedError:
        print(f"Server disconnected while downloading {url}. Retrying or handling error.")
        # Implement retry logic here
    except aiohttp.ClientConnectionError:
        print(f"Connection error while downloading {url}. Retrying or handling error.")
        # Implement retry logic here
    except Exception as e:
        print(f"An unexpected error occurred during download of {url}: {e}")

pause_event = asyncio.Event()
async def take_command():
    global pause_event
    while True:
        sys.stdout.write("Command :- ")
        sys.stdout.flush()
        message = await asyncio.to_thread(sys.stdin.readline)
        if message.strip() == "1": 
            print("Resuming downloads...")
            pause_event.set()  
        else:
            print("Pausing downloads...")
            pause_event.clear() 

#files_url = {"test1.bin":"https://ash-speed.hetzner.com/100MB.bin", "test2.bin":"https://fsn1-speed.hetzner.com/100MB.bin", "test3.bin" : "https://fsn1-speed.hetzner.com/1GB.bin"}
files_url = {"test1.bin":["https://ash-speed.hetzner.com/100MB.bin", pause_event]}


async def main():
    tasks = []
    for filename, [file_url, event] in files_url.items():
        task = asyncio.create_task(download(file_url, filename, event)) 
        tasks.append(task)

    task_commmand = asyncio.create_task(take_command())
    await asyncio.gather(*tasks, task_commmand)

if __name__ == "__main__":
    asyncio.run(main())
                    
