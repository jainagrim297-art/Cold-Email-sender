import requests
import time

# 1. SETUP YOUR KEYS
APOLLO_API_KEY = "Q8_mtYA0xa1GhNyiBxPf1A"
HUNTER_API_KEY = "dfdf8e3a939e1d9439c68b2c6289687d844d2a11"

def fetch_from_apollo(query="AI Startup"):
    """Finds founders and CEOs using Apollo's database"""
    url = "https://api.apollo.io/v1/mixed_people/search"
    headers = {"Content-Type": "application/json", "Cache-Control": "no-cache"}
    data = {
        "api_key": APOLLO_API_KEY,
        "q_keywords": query,
        "person_titles": ["Founder", "CEO", "CTO"],
        "page": 1
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json().get('people', []) if response.status_code == 200 else []

def verify_with_hunter(email):
    """Checks if the email is real to protect your sender reputation"""
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        res_data = response.json().get('data', {})
        # 'deliverable' means it's safe to send
        return res_data.get('status') == 'deliverable'
    return False

# --- MAIN EXECUTION ---
print("🚀 Starting AI Startup Lead Generation...")
leads = fetch_from_apollo()

for lead in leads:
    name = lead.get('first_name')
    company = lead.get('organization', {}).get('name')
    raw_email = lead.get('email')
    
    if raw_email:
        print(f"🔍 Verifying {name} from {company} ({raw_email})...")
        
        # Cross-check with Hunter
        if verify_with_hunter(raw_email):
            print(f"✅ VERIFIED: Preparing suitable mail for {name}...")
            
            # This is where you call your Model (CI/CD / Public Speaking AI)
            # draft = my_langchain_model.generate(name, company)
            
        else:
            print(f"❌ SKIPPED: Email for {name} might bounce.")
            
    # Respecting API rate limits for your friend's key
    time.sleep(1)