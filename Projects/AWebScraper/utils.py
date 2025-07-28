import random
import asyncio
from scraper import fetch

async def backoff_delay(attempt: int, baseDelay: float = 1.0, maxDelay: float = 30.0, jitter: bool = True):
    """ Calculate the exponential backoff delay """
    dalay = baseDelay * (2 ** (attempt - 1))
    if jitter:
        delay *= random.uniform(0.8, 1.2)
    
    return min(delay, maxDelay)

async def fetch_with_retries(session, url, retries):
    for attempt in range(retries):
        try:
            return await fetch(session, url)
        except Exception:
            if attempt < retries - 1:
                delay = backoff_delay(attempt)
                await asyncio.sleep(delay)
            else:
                print(f"Failed: {url}")
                return None
            
