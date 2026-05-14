import os
import csv
import time
import argparse
import re
from typing import List, Optional
from dotenv import load_dotenv

# Absolute imports for consistency
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from state import AgentState
from agents.scout import ScoutAgent
from agents.lead_intelligence import LeadIntelAgent
from agents.researcher import ResearcherAgent
from agents.writer import WriterAgent
from agents.sender import SenderAgent
from tools.search import SearchTool
from tools.lead_intelligence_pro import LeadIntelligencePro

load_dotenv(os.path.join(BASE_DIR, ".env"))

class OutreachBot:
    """
    Automated Outreach Bot with Human-in-the-Loop review.
    Discovery (Apollo/Search) -> Verification (Hunter) -> Intel -> Research -> Write -> Review -> Send
    """
    
    def __init__(self):
        self.scout = ScoutAgent()
        self.lead_intel = LeadIntelAgent()
        self.researcher = ResearcherAgent()
        self.writer = WriterAgent()
        self.sender = SenderAgent()
        self.search_tool = SearchTool()
        self.pro_intel = LeadIntelligencePro()

    def process_lead(self, company_name: str, target_url: str, sector: str = None, email: str = None) -> AgentState:
        """Runs the full pipeline for a single lead up to the draft stage."""
        print(f"\n[*] Processing: {company_name} ({target_url})")
        
        state: AgentState = {
            "company_name": company_name,
            "target_url": target_url or "",
            "target_segment": sector or "ML_RESEARCH",
            "hiring_manager_email": email or "",
            "hiring_manager_name": "",
            "technical_audit": [],
            "history": [],
            "email_draft": "",
            "email_sent_status": "Pending",
            "portfolio_match": {},
            "search_queries": [],
            "search_snippets": ""
        }

        # 1. Verification (Double-Check Email with Hunter)
        if state["hiring_manager_email"]:
            print(f"[*] Double-verifying email with Hunter.io for {company_name}...")
            if not self.pro_intel.verify_with_hunter(state["hiring_manager_email"]):
                print(f"[!] SKIPPED: Email {state['hiring_manager_email']} is undeliverable or risky.")
                return state

        # 2. Scout & Sector Classification
        scout_result = self.scout.run(state)
        state.update(scout_result)
        
        company_domain = state.get("target_url", "").replace("https://", "").replace("http://", "").split("/")[0]

        # 3. High-Accuracy Contact Discovery (Hunter Finder)
        if not state.get("hiring_manager_email") and state.get("hiring_manager_name"):
            print(f"[*] Attempting professional Email Discovery via Hunter Finder for {state['hiring_manager_name']}...")
            found_email = self.pro_intel.find_email_with_hunter(company_domain, state["hiring_manager_name"])
            if found_email:
                state["hiring_manager_email"] = found_email

        # 4. Fallback: Lead Intelligence (Finding emails via search/patterns)
        if not state.get("hiring_manager_email") or "example.com" in state.get("hiring_manager_email", ""):
            print(f"[*] Falling back to search-based intelligence...")
            state.update(self.lead_intel.generate_queries(state))
            state["search_snippets"] = self.search_tool.run_multi_search(state["search_queries"])
            state.update(self.lead_intel.analyze_snippets(state))
            
            # Verify the discovered email
            if state.get("hiring_manager_email"):
                if not self.pro_intel.verify_with_hunter(state["hiring_manager_email"]):
                    state["hiring_manager_email"] = ""

        if not state.get("hiring_manager_email"):
            print(f"[!] No reliable email found for {company_name}. End of pipeline.")
            return state

        # 5. Research & 6. Write Draft
        state["raw_blog_data"] = f"Deep technical work in {state['target_segment']} at {company_name}."
        state.update(self.researcher.run(state))
        state.update(self.writer.run(state))

        return state

    def fetch_apollo_leads(self, query="AI Infrastructure"):
        """Fetches high-signal leads from Apollo API."""
        print(f"[*] Fetching Pro Leads from Apollo for query: {query}...")
        results = self.pro_intel.fetch_from_apollo(query)
        leads = []
        for p in results:
            leads.append({
                "Company Name": p.get("organization", {}).get("name", "Unknown"),
                "URL": f"https://{p.get('organization', {}).get('primary_domain', '')}",
                "Email": p.get("email", ""),
                "Sector": "ML_RESEARCH", # Default
                "Name": f"{p.get('first_name', '')} {p.get('last_name', '')}"
            })
        return leads

    def run_interactive(self, leads_file: str, source: str = "csv"):
        """Main loop with source selection and automatic fallback."""
        leads = []
        if source == "apollo":
            leads = self.fetch_apollo_leads()
            if not leads:
                print("\n[!] Apollo API is restricted on your current plan. Falling back to Search-based discovery...")
                source = "search" # Trigger search fallback
        
        if source == "search":
            # Use the existing LeadGenerator search logic to find 5 fresh leads
            from leads import LeadGenerator
            generator = LeadGenerator()
            print("[*] Scouting the web for fresh high-signal leads...")
            generator.generate(batch_size=5) # This populates leads.csv
            source = "csv" # Now read from the newly populated CSV

        if source == "csv" and os.path.exists(leads_file):
            with open(leads_file, "r", encoding="utf-8") as f:
                leads = list(csv.DictReader(f))
        
        for row in leads:
            company = row.get("Company Name") or ""
            url = row.get("URL") or ""
            email = (row.get("Email") or "").strip()
            sector = (row.get("Sector") or "").strip()

            if not company: continue

            try:
                state = self.process_lead(company, url, sector, email)
                if not state.get("email_draft"): continue

                # ... Draft Review Panel (same as before) ...
                print("\n" + "█"*60)
                print(f"  DRAFT REVIEW: {company}")
                print(f"  TO: {state.get('hiring_manager_email')} ({state.get('hiring_manager_name')})")
                print("█"*60)
                print(state["email_draft"])
                print("█"*60 + "\n")

                cmd = input("Command: [s]end | [e]dit | [k]skip | [q]uit: ").lower()
                if cmd == 's':
                    print(f"[*] Sending intro to {company}...")
                    print(f"[+] Result: {self.sender.run(state)['email_sent_status']}")
                elif cmd == 'q': return
            except Exception as e:
                print(f"[!] Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OutreachBot Pro: Apollo + Hunter + AI Swarm")
    parser.add_argument("--file", default=os.path.join(BASE_DIR, "leads.csv"), help="Path to leads CSV")
    parser.add_argument("--source", choices=["csv", "apollo"], default="csv", help="Lead source")
    parser.add_argument("--test", action="store_true", help="Run a quick test lead")
    args = parser.parse_args()

    bot = OutreachBot()
    if args.test:
        bot.process_lead("Patronus AI", "https://www.patronus.ai", "CICD_AI")
    else:
        bot.run_interactive(args.file, source=args.source)