import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright
import csv
import time

# Get current script path for robust file handling
# __file__ is app/src/scrapers/startup_hunter.py
SCRAPERS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(SCRAPERS_DIR)
APP_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(APP_DIR, "data")

def run_discovery():
    print("🔍 Initializing Discovery Agent...")
    leads = []

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    with sync_playwright() as p:
        # headless=True is faster for the actual implementation
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. The Target: We are using Show HN as our hunting ground.
        target_url = "https://news.ycombinator.com/show"
        print(f"🌐 Surfing to {target_url}...")
        try:
            page.goto(target_url, timeout=60000)
            # Wait a few seconds for the page to fully load its JavaScript
            time.sleep(3) 

            # 2. The Extraction: We tell the script exactly what HTML to look for.
            print("⛏️ Mining for startup URLs...")
            
            # We look for each story row — we need both the external link AND the HN discussion link
            rows = page.locator("tr.athing").all()

            for row in rows[:15]:
                try:
                    title_el = row.locator(".titleline > a").first
                    name = title_el.inner_text().strip()
                    if name.startswith("Show HN: "):
                        name = name.replace("Show HN: ", "")

                    url = title_el.get_attribute("href")

                    # The HN discussion link is in the next sibling <tr>
                    item_id = row.get_attribute("id")
                    hn_url = f"https://news.ycombinator.com/item?id={item_id}" if item_id else ""

                    if url and url.startswith("http") and "news.ycombinator" not in url:
                        leads.append({"Company": name, "URL": url, "HN_URL": hn_url})
                        print(f"✅ Found Lead: {name}")
                except Exception:
                    continue
        except Exception as e:
            print(f"❌ Playwright Error: {e}")
        finally:
            print("🚪 Closing browser...")
            browser.close()

    # 3. Save to Database (CSV)
    target_path = os.path.join(DATA_DIR, "target_leads.csv")
    print(f"\n💾 Saving {len(leads)} fresh leads to {target_path}...")
    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Company", "URL", "HN_URL"])
        writer.writeheader()
        writer.writerows(leads)

    print("🚀 Discovery Complete! The hunting phase is done.")

if __name__ == "__main__":
    run_discovery()