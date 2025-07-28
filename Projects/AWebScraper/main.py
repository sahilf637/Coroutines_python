from tqdm import tqdm
import asyncio
import aiohttp
import csv
from utils import fetch_with_retries

def save_to_csv(results):
    with open("results.csv", "w", newline="") as fs:
        writer = csv.writer(fs)
        writer.writerow(["url", "Content"])
        for url, content in results:
            writer.writerow([url, (content or "")[:100]])

async def main():
    urls = [
        "http://books.toscrape.com/",
        "http://quotes.toscrape.com/",
        "https://scrapethissite.com/",
        "https://www.scrapingcourse.com/ecommerce/",
        "https://oxylabs.io/products/scraping-sandbox",
        "https://en.wikipedia.org/wiki/List_of_SpongeBob_SquarePants_episodes",
        "https://finance.yahoo.com/",
        "https://old.reddit.com/",
        "https://data.gov/",
        "https://www.imdb.com/chart/top",
    ]

    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            task = asyncio.create_task(fetch_with_retries(session, url, 3))
            tasks.append((task, url))

        results = []

        for completed_task in tqdm(asyncio.as_completed([task for task, _ in tasks]), total=len(tasks)):
            # Find the original URL by iterating through the stored tasks
            # A more efficient way would be to use a dictionary mapping task ID to URL,
            # but for a small number of tasks, this is acceptable.
            original_url = None
            for original_task, url in tasks:
                if completed_task is original_task: # Check for identity
                    original_url = url
                    break

            if original_url:
                content = await completed_task
                results.append((original_url, content or ""))
            else:
                # This case should ideally not happen if everything is set up correctly
                print(f"Warning: Could not find original URL for completed task: {completed_task}")


    save_to_csv(results)

if __name__ == "__main__":
    asyncio.run(main())