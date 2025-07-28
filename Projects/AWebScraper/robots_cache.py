# robots_cache.py
import asyncio
import aiohttp
from urllib.parse import urlparse
from collections import defaultdict
import time
import re

# This class will now handle parsing and rule checking for robots.txt
class SimplifiedRobotsParser:
    def __init__(self, content: str):
        # Stores rules per user-agent. '*' is the default.
        # Format: { 'user_agent': {'disallow': [regex_pattern, ...], 'allow': [regex_pattern, ...]} }
        self.rules = defaultdict(lambda: {'disallow': [], 'allow': []})
        self.crawl_delays = defaultdict(float)

        self._parse_content(content)

    def _parse_content(self, content: str):
        current_user_agents = []
        lines = content.splitlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split(':', 1)
            if len(parts) < 2:
                continue
            
            directive = parts[0].strip().lower()
            value = parts[1].strip()

            if directive == 'user-agent':
                # When a new User-agent block starts, clear current_user_agents
                # unless it's the first block or a continuation
                if current_user_agents and not current_user_agents[-1] == value.lower():
                    # If the last UA was not this one, and we are not starting a new block of the same UA
                    # This logic handles multiple UA lines for one block (e.g., User-agent: A \n User-agent: B)
                    # and also new blocks (User-agent: A \n Disallow: / \n User-agent: B)
                    # Simple heuristic: if we encounter a new user-agent, the previous block is done.
                    # This isn't perfect for all robots.txt variations but covers common cases.
                    current_user_agents = [value.lower()]
                elif not current_user_agents: # First user-agent encountered
                    current_user_agents.append(value.lower())
                elif value.lower() not in current_user_agents: # Add to current block
                     current_user_agents.append(value.lower())
            
            elif current_user_agents: # Apply rules to the current_user_agents block
                # Convert robots.txt pattern to regex pattern
                # '*' -> '.*' (match any characters)
                # '$' -> '$' (match end of string)
                # Escape other regex special characters
                if value == '': # Empty Disallow/Allow typically means allow all/disallow all for that context
                     pattern = '' # Special case for empty
                else:
                    # Escape, then replace special robots.txt wildcards
                    pattern = re.escape(value).replace(r'\*', '.*').replace(r'\$', '$')

                if directive == 'disallow':
                    for ua in current_user_agents:
                        self.rules[ua]['disallow'].append(pattern)
                elif directive == 'allow':
                    for ua in current_user_agents:
                        self.rules[ua]['allow'].append(pattern)
                elif directive == 'crawl-delay':
                    try:
                        delay = float(value)
                        for ua in current_user_agents:
                            self.crawl_delays[ua] = delay
                    except ValueError:
                        pass # Ignore invalid crawl-delay value

    def _get_applicable_rules(self, user_agent: str):
        """Returns the disallow and allow rules that apply to the given user_agent."""
        user_agent_lower = user_agent.lower()

        # Prioritize specific user-agent rules over '*' wildcard rules
        if user_agent_lower in self.rules:
            return self.rules[user_agent_lower]['disallow'], self.rules[user_agent_lower]['allow']
        elif '*' in self.rules:
            return self.rules['*']['disallow'], self.rules['*']['allow']
        
        # If no rules found for specific or wildcard, default to empty
        return [], []

    def can_fetch(self, user_agent: str, path: str) -> bool:
        """Checks if the given path is allowed for the user_agent based on robots.txt rules."""
        path = path if path.startswith('/') else '/' + path # Ensure path starts with /

        disallow_patterns, allow_patterns = self._get_applicable_rules(user_agent)

        # Find the longest matching disallow rule
        longest_disallow_match_len = -1
        is_disallowed = False
        for pattern in disallow_patterns:
            if pattern == '': # Empty Disallow rule means Allow all. Overrides any potential disallow.
                is_disallowed = False # But still check allow rules below
                continue
            
            # re.match starts matching from the beginning of the string
            # re.fullmatch would match the entire string
            # For robots.txt, we usually check if the path *starts* with the pattern.
            # And pattern has been converted to regex for that purpose.
            if re.match(pattern, path):
                if len(pattern) > longest_disallow_match_len:
                    longest_disallow_match_len = len(pattern)
                    is_disallowed = True

        # Find the longest matching allow rule
        longest_allow_match_len = -1
        is_allowed = False
        for pattern in allow_patterns:
            if pattern == '': # Empty Allow rule typically means "Allow this part" but for a regex it's tricky.
                # If an explicit Allow: rule, it implies allow.
                is_allowed = True # Simplistic: any empty allow means "allow this".
                continue

            if re.match(pattern, path):
                if len(pattern) > longest_allow_match_len:
                    longest_allow_match_len = len(pattern)
                    is_allowed = True

        # Rule precedence: Longest match wins. If lengths are equal, Allow usually wins.
        # This is the "most specific rule wins" part.
        if is_allowed and is_disallowed:
            if longest_allow_match_len > longest_disallow_match_len:
                return True
            elif longest_disallow_match_len > longest_allow_match_len:
                return False
            else: # Lengths are equal, Allow typically takes precedence
                return True # Default to allowed if rules are ambiguous/equal length
        elif is_allowed:
            return True # Only allow rules matched
        elif is_disallowed:
            return False # Only disallow rules matched
        
        # Default behavior if no specific rules match: allowed
        return True

    def get_crawl_delay(self, user_agent: str) -> float:
        user_agent_lower = user_agent.lower()
        if user_agent_lower in self.crawl_delays:
            return self.crawl_delays[user_agent_lower]
        if '*' in self.crawl_delays:
            return self.crawl_delays['*']
        return 0.0 # No specific crawl delay

class RobotTextCache:
    def __init__(self):
        # Stores (SimplifiedRobotsParser instance, last_fetched_time)
        self._cache = defaultdict(lambda: (None, 0)) # Default to (None, 0)
        self._fetch_in_progress = defaultdict(asyncio.Lock) # To prevent multiple fetches for the same robots.txt

    async def _fetch_robot_txt(self, session: aiohttp.ClientSession, netloc: str):
        robots_urls = [f"https://{netloc}/robots.txt", f"http://{netloc}/robots.txt"]
        
        async with self._fetch_in_progress[netloc]:
            # Check cache freshness *after* acquiring lock
            parser_from_cache, last_fetched_time = self._cache[netloc]
            if parser_from_cache is not None and (time.time() - last_fetched_time) < 3600:
                return parser_from_cache

            parser_instance = None
            for robots_url in robots_urls:
                try:
                    # Using a short timeout for robots.txt fetching
                    async with session.get(robots_url, timeout=5) as response:
                        if response.status == 200:
                            content = await response.text()
                            parser_instance = SimplifiedRobotsParser(content)
                            self._cache[netloc] = (parser_instance, time.time())
                            print(f"Fetched and cached robots.txt for {netloc} from {robots_url}")
                            return parser_instance
                        elif response.status == 404:
                            print(f"robots.txt not found for {netloc} at {robots_url}. Defaulting to allow-all.")
                            parser_instance = SimplifiedRobotsParser("") # Empty content means allow-all
                            self._cache[netloc] = (parser_instance, time.time())
                            return parser_instance
                        else:
                            print(f"Could not fetch robots.txt for {netloc} from {robots_url}. Status: {response.status}")
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    print(f"Error fetching robots.txt for {netloc} from {robots_url}: {e}")
            
            # If all attempts fail or non-200/404, default to allow-all
            print(f"Failed to fetch robots.txt for {netloc} after all attempts. Defaulting to allow-all.")
            parser_instance = SimplifiedRobotsParser("") # Empty parser effectively allows all
            self._cache[netloc] = (parser_instance, time.time())
            return parser_instance
            
    async def is_allowed(self, session: aiohttp.ClientSession, url: str, user_agent: str) -> bool:
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc
        # Ensure path is always non-empty and starts with '/'
        path = parsed_url.path if parsed_url.path else '/'

        if not netloc:
            return True # Cannot parse domain, assume allowed

        # Retrieve from cache or fetch if not present/stale
        parser_instance, last_fetched_time = self._cache[netloc] # Using self._cache[netloc] relies on defaultdict

        if parser_instance is None or (time.time() - last_fetched_time) > 3600:
            parser_instance = await self._fetch_robot_txt(session, netloc)
        
        # At this point, parser_instance should never be None due to _fetch_robot_txt logic
        if not parser_instance:
            print(f"Warning: No robots.txt parser instance for {netloc}. Assuming allowed.")
            return True

        return parser_instance.can_fetch(user_agent, path)

# Global instance
robots_cache = RobotTextCache()