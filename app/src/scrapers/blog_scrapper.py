import os
import re
import json  # <--- Added here at the top
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from src.processor.models import RawSignal
from dotenv import load_dotenv

load_dotenv()

class BlogScraper:
    def __init__(self):
        self.headless = os.getenv("DEBUG_MODE", "true").lower() == "false"

    def extract_date(self, url: str, html: str) -> datetime | None:
        """Hunts for the publication date in meta tags, JSON-LD, or URL."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Strategy 1: JSON-LD (The modern standard used by OpenAI & Medium)
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                # Sometimes JSON-LD is a list, sometimes a dict
                if isinstance(data, list): 
                    data = data[0]
                
                # Check for common date keys
                date_str = data.get("datePublished") or data.get("dateModified")
                if date_str:
                    return datetime.fromisoformat(date_str.split('T')[0])
            except:
                continue

        # Strategy 2: Standard Meta Tags
        meta_tags = [
            soup.find("meta", property="article:published_time"),
            soup.find("meta", {"name": "pubdate"})
        ]
        
        for tag in meta_tags:
            if tag and tag.get("content"):
                try:
                    return datetime.fromisoformat(tag["content"].split('T')[0])
                except ValueError:
                    continue

        # Strategy 3: URL Pattern (e.g., /2024/05/post-title)
        url_match = re.search(r'/(\d{4})/(\d{2})/', url)
        if url_match:
            return datetime(year=int(url_match.group(1)), month=int(url_match.group(2)), day=1)
            
        return None

    async def scrape_post(self, url: str, source_name: str) -> RawSignal:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await stealth_async(page)
            
            print(f"🌐 Scraping: {url}")
            
            # --- FIX: Changed to networkidle and added a short wait ---
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(2000) # Give React/Medium time to render
            
            html_content = await page.content()
            title = await page.title()
            
            await browser.close()
            
            # Find the date
            published_date = self.extract_date(url, html_content)
            
            return RawSignal(
                title=title,
                url=url,
                raw_html=html_content,
                source=source_name,
                published_at=published_date
            )