import asyncio
import requests
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

class LinkedInScraper:
    """Free alternative: Basic web scraping instead of paid Proxycurl API."""
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def get_company_details(self, company_url: str):
        # We target their main website since LinkedIn blocks requests without paid APIs
        try:
            response = requests.get(company_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "")
                
            return {
                "name": soup.title.string if soup.title else "Unknown",
                "description": description
            }
        except Exception as e:
            return {"error": str(e)}

class WebScraper:
    """Uses open-source Crawl4AI for free browser-based markdown extraction."""
    def __init__(self):
        pass

    def scrape_to_markdown(self, url: str):
        async def fetch():
            try:
                # Use a specific browser context to ensure cleaner closure
                async with AsyncWebCrawler(verbose=False) as crawler:
                    result = await crawler.arun(url=url)
                    return result.markdown
            except Exception:
                return ""
        
        try:
            # On Windows, asyncio.run can trigger noisy cleanup warnings
            return asyncio.run(fetch())
        except (RuntimeError, ValueError) as e:
            # Check if it's the known Windows 'closed pipe' issue
            if "closed pipe" in str(e):
                return "" # Silent fail on cleanup issues
            raise e
