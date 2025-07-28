import urllib.parse
from collections import defaultdict
import asyncio
import time

class RateLimiter:
    def __init__(self, delay = 2):
        self.domain_last_called = defaultdict(lambda: 0)
        self.delay = delay
    
    async def wait(self, domain):
        elapsed = time.time() - self.domain_last_called[domain]
        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)
        
        self.domain_last_called[domain] = time.time()

rate_limiter = RateLimiter(delay=2)

async def fetch(session, url):
    domain = urllib.parse.urlparse(url).netloc
    await rate_limiter.wait(domain)

    try:
        async with session.get(url) as response:
            return await response.text()
    
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None