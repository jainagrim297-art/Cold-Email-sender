import os
import requests
import sys
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

def test_hunter():
    if not HUNTER_API_KEY:
        print("❌ Error: HUNTER_API_KEY not found in .env")
        return
    
    domain = "google.com"
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}"
    
    print(f"Testing Hunter.io for domain: {domain}...")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                print(f"✅ Success! Found {len(data['data'].get('emails', []))} emails for {domain}")
            else:
                print(f"⚠️ Warning: Response 200 but no data field. {data}")
        else:
            print(f"❌ Failed: Status code {response.status_code}. {response.text}")
    except Exception as e:
        print(f"❌ Error during request: {e}")

if __name__ == "__main__":
    test_hunter()
