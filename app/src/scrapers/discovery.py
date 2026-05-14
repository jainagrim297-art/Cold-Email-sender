from duckduckgo_search import DDGS
import time

class AutonomousDiscovery:
    def __init__(self):
        # Initialize the DuckDuckGo search client
        self.ddgs = DDGS()

    def find_startup_blogs(self, query: str, max_results: int = 5) -> list:
        """
        Searches the web for specific startup footprints and extracts the URLs.
        """
        print(f"\n🕵️‍♂️ AUTONOMOUS DISCOVERY: Searching the web for -> '{query}'")
        discovered_targets = []
        
        try:
            # Execute the search
            results = self.ddgs.text(query, max_results=max_results)
            
            for result in results:
                url = result.get('href')
                title = result.get('title')
                if url:
                    discovered_targets.append({
                        "url": url,
                        "source": f"Discovered: {title[:30]}..."
                    })
            
            print(f"🎯 Found {len(discovered_targets)} potential startup blogs.")
            return discovered_targets
            
        except Exception as e:
            print(f"❌ Search Error: {e}")
            return []