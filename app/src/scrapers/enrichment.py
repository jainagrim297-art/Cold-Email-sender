"""
Lead Enrichment Orchestrator
=============================
Priority chain:
  1. Custom Email Discovery Engine (free — scraping + SMTP ping + search)
  2. Hunter.io  (API key required)
  3. Apollo.io  (API key required)
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

from scrapers.email_discovery import discover_email, extract_domain, GENERIC_HOSTS

load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")


# ─────────────────────────────────────────────────────────────────────────────
# Fallback 1: Hunter.io
# ─────────────────────────────────────────────────────────────────────────────

def get_contact_email_hunter(domain: str) -> str | None:
    if not HUNTER_API_KEY:
        return None
    print(f"  [Hunter] Querying Hunter.io for {domain}...")
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={HUNTER_API_KEY}"
    try:
        data = requests.get(url, timeout=10).json()
        if "data" in data and data["data"].get("emails"):
            email = data["data"]["emails"][0]["value"]
            print(f"  [Hunter] Found: {email}")
            return email
    except Exception as e:
        print(f"  [Hunter] Error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Fallback 2: Apollo.io
# ─────────────────────────────────────────────────────────────────────────────

def get_contact_email_apollo(domain: str) -> str | None:
    if not APOLLO_API_KEY:
        return None
    print(f"  [Apollo] Querying Apollo for {domain}...")
    try:
        data = requests.post(
            "https://api.apollo.io/v1/people/search",
            json={"api_key": APOLLO_API_KEY, "q_organization_domains": domain, "page": 1},
            headers={"Content-Type": "application/json"},
            timeout=10,
        ).json()
        for person in data.get("people", []):
            if person.get("email"):
                print(f"  [Apollo] Found: {person['email']}")
                return person["email"]
    except Exception as e:
        print(f"  [Apollo] Error: {e}")
    return None


def get_contact_email(domain: str) -> str | None:
    """
    Tries Hunter.io first, then Apollo.io as a fallback.
    """
    if not domain:
        return None
    
    email = get_contact_email_hunter(domain)
    if email:
        return email
        
    return get_contact_email_apollo(domain)


# ─────────────────────────────────────────────────────────────────────────────
# Main Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def find_best_email(website_url: str, hn_url: str = None) -> str | None:
    """
    Tries all available methods to find a contact email.
    Priority: Custom Discovery → Hunter.io → Apollo.io
    """
    print(f"\n🔎 Enriching lead: {website_url}")

    # Priority 1: Custom free engine
    email = discover_email(website_url, hn_post_url=hn_url)
    if email:
        print(f"✅ [Custom Engine] Found: {email}")
        return email

    # Priority 2: API Enrichment (Hunter -> Apollo)
    domain = extract_domain(website_url)
    if domain:
        # Quality check: If it's a generic host (GitHub/GitLab), we skip Hunter/Apollo
        # because those results (e.g. smithfrancois@github.com) are rarely founders.
        if domain in GENERIC_HOSTS:
            print(f"  [QUALITY] Skipping generic host ({domain}) for Hunter/Apollo enrichment.")
            return None

        return get_contact_email(domain)

    print(f"❌ All methods exhausted. No email found for {website_url}")
    return None


if __name__ == "__main__":
    # Quick test
    tests = [
        "https://fluidcad.io/",
        "https://cssstudio.ai",
        "https://www.unlegacy.ai/",
    ]
    for url in tests:
        result = find_best_email(url)
        print(f"\n>>> FINAL: {url} → {result}\n{'─'*60}")
