import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

class LeadIntelligencePro:
    """
    Advanced Lead Intelligence using Apollo.io for discovery 
    and Hunter.io for double-verification.
    """
    
    @staticmethod
    def fetch_from_apollo(query="AI Startup", page=1):
        """Finds founders and CEOs using Apollo's database"""
        if not APOLLO_API_KEY:
            print("[!] APOLLO_API_KEY not found in .env")
            return []
            
        url = "https://api.apollo.io/v1/mixed_people/search"
        headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": APOLLO_API_KEY
        }
        data = {
            "q_keywords": query,
            "person_titles": ["Founder", "CEO", "CTO", "Head of Engineering"],
            "page": page
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                return response.json().get('people', [])
            else:
                print(f"[!] Apollo Error {response.status_code}: {response.text}")
                return []
        except Exception as e:
            print(f"[!] Apollo Connection Failed: {e}")
            return []

    @staticmethod
    def verify_with_hunter(email):
        """Checks if the email is real to protect sender reputation"""
        if not HUNTER_API_KEY:
            print("[!] HUNTER_API_KEY not found in .env")
            return False 
            
        url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_API_KEY}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                res_data = response.json().get('data', {})
                status = res_data.get('status')
                print(f"[*] Hunter Verification: {email} -> {status}")
                return status == 'deliverable'
            return False
        except Exception:
            return False

    @staticmethod
    def find_email_with_hunter(domain, full_name):
        """Uses Hunter.io's professional finder to get the exact email."""
        if not HUNTER_API_KEY or not domain or not full_name:
            return None
            
        # Split name for Hunter API
        parts = full_name.split()
        first_name = parts[0]
        last_name = parts[-1] if len(parts) > 1 else ""
        
        url = "https://api.hunter.io/v2/email-finder"
        params = {
            "domain": domain,
            "first_name": first_name,
            "last_name": last_name,
            "api_key": HUNTER_API_KEY
        }
        
        try:
            print(f"[*] Hunter Finder: Searching for {full_name} at {domain}...")
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json().get('data', {})
                email = data.get('email')
                score = data.get('score', 0)
                if email and score >= 80: # Highly accurate
                    print(f"[+] Hunter Found Verified Email: {email} (Score: {score})")
                    return email
            return None
        except Exception:
            return None

if __name__ == "__main__":
    # Test
    pro = LeadIntelligencePro()
    leads = pro.fetch_from_apollo("MLOps AI")
    if leads:
        first = leads[0]
        email = first.get("email")
        if email:
            is_valid = pro.verify_with_hunter(email)
            print(f"Test Lead: {first.get('name')} -> {email} -> Valid: {is_valid}")
