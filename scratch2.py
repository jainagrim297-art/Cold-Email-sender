from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

def get_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page)
        
        page.goto("https://theresanaiforthat.com/new/")
        page.wait_for_timeout(5000)
        
        # get all <a> tags with an href
        links = page.locator("a").element_handles()
        valid = 0
        for link in links:
            href = link.get_attribute("href")
            cls = link.get_attribute("class")
            text = link.inner_text().strip()
            if text and href and "https://www.cloudflare.com" not in href:
                print(f"Class: {cls} | Href: {href} | Text: {text}")
                valid += 1
                if valid > 20: break
                
        browser.close()

if __name__ == "__main__":
    get_links()
