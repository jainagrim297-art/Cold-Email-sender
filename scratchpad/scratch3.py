from playwright.sync_api import sync_playwright

def get_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://news.ycombinator.com/show")
        page.wait_for_timeout(3000)
        
        # get all titleline links
        elements = page.locator(".titleline > a").all()
        for element in elements[:10]:
            href = element.get_attribute("href")
            text = element.inner_text().strip()
            if text and href:
                print(f"Href: {href} | Text: {text}")
                
        browser.close()

if __name__ == "__main__":
    get_links()
