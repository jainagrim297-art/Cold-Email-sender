from playwright.sync_api import sync_playwright

def get_links():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://theresanaiforthat.com/new/")
        page.wait_for_timeout(3000)
        
        # get all <a> tags with an href
        links = page.locator("a").element_handles()
        for link in links[:30]:
            href = link.get_attribute("href")
            cls = link.get_attribute("class")
            text = link.inner_text().strip()
            if text and href:
                print(f"Class: {cls} | Href: {href} | Text: {text}")
                
        browser.close()

if __name__ == "__main__":
    get_links()
