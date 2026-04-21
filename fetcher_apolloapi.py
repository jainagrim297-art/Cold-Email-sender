import requests

# Your friend's Apollo API Key
APOLLO_API_KEY = "Q8_mtYA0xa1GhNyiBxPf1A"

def fetch_ai_startups(query="AI Startup"):
    url = "https://api.apollo.io/v1/mixed_people/search"
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    }
    
    # We are searching for Founders/CEOs in AI companies
    data = {
        "api_key": APOLLO_API_KEY,
        "q_keywords": query,
        "person_titles": ["Founder", "CEO", "CTO"],
        "page": 1
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get('people', [])
        else:
            print(f"Error: {response.status_code} - Check if the key is still active.")
            return []
    except Exception as e:
        print(f"Connection failed: {e}")
        return []

# --- Run the search ---
leads = fetch_ai_startups()

for lead in leads:
    name = lead.get('first_name', 'there')
    company = lead.get('organization', {}).get('name', 'your startup')
    email = lead.get('email')
    
    if email:
        print(f"Target Found: {name} @ {company} -> {email}")
        # Next step: Pass this to your AI model logic