"""
Custom Email Discovery & Verification Engine
=============================================
Finds real founder emails using 4 layered strategies:

  Layer 1 — Contact Page Scraping: Scrapes /contact, /about, /team pages
             for mailto: links. Zero cost, zero API.
  Layer 2 — Pattern Generation + SMTP Verification: Guesses common email
             patterns (first@domain, first.last@domain, etc.) and
             "pings" the mail server via SMTP to verify existence.
             No email is ever actually sent.
  Layer 3 — Search Mining: Uses DuckDuckGo to find publicly listed emails.
  Layer 4 — Hunter/Apollo fallback (kept in enrichment.py).
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import re
import socket
import smtplib
import requests
import dns.resolver
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from itertools import product

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Roles that indicate a senior/founder contact
FOUNDER_SIGNALS = [
    "founder", "co-founder", "cofounder", "ceo", "chief executive",
    "cto", "chief technology", "president", "director", "head of",
]

# Skip generic hosts — no point pinging github.com or codeberg.org
GENERIC_HOSTS = {
    "github.com", "gitlab.com", "codeberg.org",
    "medium.com", "substack.com", "twitter.com",
    "linkedin.com", "youtube.com", "reddit.com",
}


def extract_domain(url: str) -> str:
    """Extracts clean domain from any URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.strip("/")
    except Exception:
        return ""


def fetch_page(url: str, timeout: int = 8) -> BeautifulSoup | None:
    """Fetches a URL and returns a BeautifulSoup object."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 1 — Scrape Contact / About / Team pages for mailto: links
# ─────────────────────────────────────────────────────────────────────────────

CONTACT_PATHS = [
    "/", "/contact", "/contact-us", "/about", "/about-us",
    "/team", "/founders", "/people", "/company", "/hello",
]


def scrape_mailto_links(base_url: str) -> list[str]:
    """
    Crawls common contact pages for mailto: links.
    Returns a list of discovered email addresses.
    """
    domain = extract_domain(base_url)
    found_emails = set()
    scheme = urlparse(base_url).scheme or "https"
    root = f"{scheme}://{domain}"

    print(f"  [L1] Scraping contact pages for mailto: links...")

    for path in CONTACT_PATHS:
        url = root + path
        soup = fetch_page(url)
        if not soup:
            continue

        # Find all <a href="mailto:..."> tags
        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0].strip().lower()
                if EMAIL_RE.match(email) and domain in email:
                    found_emails.add(email)

        # Also scan raw page text using regex (some sites use obfuscated spans)
        raw = soup.get_text(" ")
        for match in EMAIL_RE.findall(raw):
            if domain in match.lower():
                found_emails.add(match.lower())

    if found_emails:
        print(f"  [L1] Found via page scrape: {found_emails}")

    return list(found_emails)


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2a — Extract founder names from About / Team pages
# ─────────────────────────────────────────────────────────────────────────────

def extract_founder_name(base_url: str) -> tuple[str, str] | None:
    """
    Tries to extract a founder's first and last name from an About/Team page.
    Returns (first_name, last_name) or None.
    """
    domain = extract_domain(base_url)
    scheme = urlparse(base_url).scheme or "https"
    root = f"{scheme}://{domain}"

    name_pages = ["/about", "/team", "/about-us", "/company", "/founders"]

    for path in name_pages:
        soup = fetch_page(root + path)
        if not soup:
            continue

        # Look for name near founder-signal words
        text = soup.get_text(" ").lower()
        for signal in FOUNDER_SIGNALS:
            idx = text.find(signal)
            if idx != -1:
                # Grab a 200-char window around the signal
                window = soup.get_text(" ")[max(0, idx - 100): idx + 200]
                # Match a "Firstname Lastname" pattern (capitalized words)
                names = re.findall(r"\b([A-Z][a-z]{1,15})\s+([A-Z][a-z]{1,20})\b", window)
                for first, last in names:
                    # Skip common non-name words
                    if first.lower() not in {"head", "chief", "senior", "vice", "our", "the", "meet"}:
                        print(f"  [L2a] Guessed founder: {first} {last}")
                        return first.lower(), last.lower()

    return None


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2b — Generate email patterns from a name + domain
# ─────────────────────────────────────────────────────────────────────────────

def generate_patterns(first: str, last: str, domain: str) -> list[str]:
    """Generates the 6 most common corporate email patterns for a name."""
    f, l = first.lower().strip(), last.lower().strip()
    fi = f[0] if f else ""
    li = l[0] if l else ""
    return [
        f"{f}@{domain}",
        f"{f}.{l}@{domain}",
        f"{f}{l}@{domain}",
        f"{fi}{l}@{domain}",
        f"{f}_{l}@{domain}",
        f"{f}.{li}@{domain}",
    ]


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2c — SMTP Verification (the "Ping" method)
# ─────────────────────────────────────────────────────────────────────────────

def get_mx_host(domain: str) -> str | None:
    """Looks up the MX record for a domain to find its mail server."""
    try:
        records = dns.resolver.resolve(domain, "MX")
        # Sort by preference (lowest = highest priority)
        mx = sorted(records, key=lambda r: r.preference)[0]
        return str(mx.exchange).rstrip(".")
    except Exception:
        return None


def smtp_verify(email: str, mx_host: str, sender_domain: str = "gmail.com") -> bool:
    """
    Connects to the mail server and asks if the email address exists.
    Uses the SMTP RCPT TO handshake — NO email is ever sent.
    Returns True if the server confirms the address.
    """
    try:
        with smtplib.SMTP(timeout=8) as smtp:
            smtp.connect(mx_host, 25)
            smtp.ehlo(sender_domain)
            smtp.mail(f"verify@{sender_domain}")
            code, _ = smtp.rcpt(email)
            smtp.quit()
            return code == 250
    except smtplib.SMTPConnectError:
        # Port 25 blocked by ISP (common on home connections)
        return False
    except smtplib.SMTPServerDisconnected:
        return False
    except socket.timeout:
        return False
    except Exception:
        return False


def verify_pattern_list(patterns: list[str], domain: str) -> str | None:
    """
    Gets the MX host once, then SMTP-pings each pattern.
    Returns the first verified email, or None.
    """
    mx = get_mx_host(domain)
    if not mx:
        print(f"  [L2c] No MX record found for {domain}. Skipping SMTP ping.")
        return None

    print(f"  [L2c] MX host: {mx}. Pinging {len(patterns)} patterns...")
    for email in patterns:
        result = smtp_verify(email, mx)
        status = "✅ 250 OK" if result else "❌ no match"
        print(f"         {email} → {status}")
        if result:
            return email

    return None


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2d — Generic SMTP Ping (no name needed)
# ─────────────────────────────────────────────────────────────────────────────

GENERIC_PATTERNS = [
    "hello", "hi", "contact", "founders", "founder",
    "ceo", "team", "info", "jobs", "work",
]


def try_generic_smtp(domain: str) -> str | None:
    """
    Tries common generic email prefixes (hello@, contact@, founder@)
    via SMTP ping. Used as a fallback when no founder name can be found.
    """
    mx = get_mx_host(domain)
    if not mx:
        return None

    # Skip obvious catch-all / forwarding-only hosts
    FORWARDER_HINTS = ["registrar-servers", "parkingpage", "parked", "sedoparking"]
    if any(h in mx for h in FORWARDER_HINTS):
        print(f"  [L2d] MX is a registrar forwarder ({mx}). Skipping generic ping.")
        return None

    print(f"  [L2d] Trying {len(GENERIC_PATTERNS)} generic patterns on {domain}...")
    for prefix in GENERIC_PATTERNS:
        email = f"{prefix}@{domain}"
        result = smtp_verify(email, mx)
        status = "✅ 250 OK" if result else "❌"
        print(f"         {email} → {status}")
        if result:
            return email
    return None


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 2e — Hacker News Poster Profile Scraping
# ─────────────────────────────────────────────────────────────────────────────

def get_hn_poster_name(hn_post_url: str) -> tuple[str, str] | None:
    """
    Given a HN post URL, finds the poster's username and scrapes their
    HN profile for a real name (often listed in the 'about' field)
    or their GitHub profile URL.
    Returns (first, last) or None.
    """
    if not hn_post_url:
        return None
    try:
        soup = fetch_page(hn_post_url)
        if not soup:
            return None

        # Find "X hours ago by username" text
        user_link = soup.find("a", class_="hnuser")
        if not user_link:
            return None

        username = user_link.get_text(strip=True)
        profile_url = f"https://news.ycombinator.com/user?id={username}"
        profile = fetch_page(profile_url)
        if not profile:
            return None

        # Check the 'about' field for a real name or GitHub link
        about_td = profile.find("td", string=lambda t: t and "about" in t.lower())
        if about_td:
            about_text = about_td.find_next_sibling("td")
            if about_text:
                text = about_text.get_text(" ")
                names = re.findall(r"\b([A-Z][a-z]{1,14})\s+([A-Z][a-z]{1,20})\b", text)
                if names:
                    first, last = names[0]
                    print(f"  [L2e] HN profile name: {first} {last}")
                    return first.lower(), last.lower()

        # HN username itself is sometimes a name (e.g. "johndoe" → john, doe)
        # Try to split if it looks like firstlast
        if len(username) > 5 and username.isalpha():
            mid = len(username) // 2
            print(f"  [L2e] Guessing name from HN username: {username}")
            return username[:mid], username[mid:]

    except Exception as e:
        print(f"  [L2e] HN scrape error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# LAYER 3 — DuckDuckGo Search Mining
# ─────────────────────────────────────────────────────────────────────────────

DDG_URL = "https://html.duckduckgo.com/html/"


def search_mine_email(domain: str) -> str | None:
    """
    Uses DuckDuckGo to search for publicly visible emails from the domain.
    Searches for: "@domain.com" contact founder
    """
    print(f"  [L3] Mining DuckDuckGo for public emails at {domain}...")
    query = f'"@{domain}" founder OR contact OR "reach us"'
    try:
        r = requests.post(
            DDG_URL,
            data={"q": query, "kl": "wt-wt"},
            headers=HEADERS,
            timeout=8,
        )
        soup = BeautifulSoup(r.text, "html.parser")
        raw = soup.get_text(" ")
        matches = EMAIL_RE.findall(raw)
        for m in matches:
            if domain in m.lower():
                print(f"  [L3] Found via search: {m.lower()}")
                return m.lower()
    except Exception as e:
        print(f"  [L3] DuckDuckGo search error: {e}")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def discover_email(website_url: str, hn_post_url: str = None) -> str | None:
    """
    Orchestrates all discovery layers for a given startup URL.

    Pipeline:
      L1 — Scrape contact pages for mailto: links
      L2a — Extract founder name from About/Team page
      L2b — Generate email patterns from founder name
      L2c — SMTP-ping the pattern list
      L2d — SMTP-ping generic prefixes (hello@, contact@, founder@)
      L2e — Scrape HN poster's profile for a real name → L2b+L2c again
      L3  — DuckDuckGo search mining

    Returns the best verified email found, or None.
    """
    domain = extract_domain(website_url)
    if not domain:
        return None

    if domain in GENERIC_HOSTS:
        print(f"  [SKIP] {domain} is a generic host — no specific email to find.")
        return None

    print(f"\n--- Email Discovery for: {domain} ---")

    # ── Layer 1: Scrape mailto: links from contact/about pages ──
    emails = scrape_mailto_links(website_url)
    if emails:
        LOW_QUALITY = {"info", "support", "hello", "abuse", "noreply", "no-reply",
                       "contact", "team", "admin", "press", "media", "legal"}
        preferred = [e for e in emails if e.split("@")[0] not in LOW_QUALITY]
        return preferred[0] if preferred else emails[0]

    # ── Layer 2a-c: About/Team page name → patterns → SMTP ping ──
    name = extract_founder_name(website_url)
    if name:
        first, last = name
        patterns = generate_patterns(first, last, domain)
        print(f"  [L2b] Generated {len(patterns)} patterns for {first} {last}:")
        for p in patterns:
            print(f"         {p}")
        verified = verify_pattern_list(patterns, domain)
        if verified:
            return verified

    # ── Layer 2d: Generic prefix SMTP ping ──
    generic = try_generic_smtp(domain)
    if generic:
        return generic

    # ── Layer 2e: HN poster profile → name → patterns → SMTP ping ──
    if hn_post_url:
        hn_name = get_hn_poster_name(hn_post_url)
        if hn_name:
            first, last = hn_name
            patterns = generate_patterns(first, last, domain)
            print(f"  [L2e+L2b] Pinging HN-derived patterns for {first} {last}...")
            verified = verify_pattern_list(patterns, domain)
            if verified:
                return verified

    # ── Layer 3: DuckDuckGo search mining ──
    email = search_mine_email(domain)
    if email:
        return email

    print(f"  [RESULT] No email found for {domain}.")
    return None


if __name__ == "__main__":
    # Quick self-test
    tests = [
        "https://fluidcad.io/",
        "https://cssstudio.ai",
        "https://www.unlegacy.ai/",
    ]
    for url in tests:
        result = discover_email(url)
        print(f"\n>>> RESULT for {url}: {result}\n{'─'*60}")
