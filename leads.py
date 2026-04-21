import os
import csv
import argparse
from dotenv import load_dotenv
from typing import List, Set
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.search import SearchTool

load_dotenv()

class LeadGenerator:
    """Intelligent lead generation for intern_agent."""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.7)
        self.search_tool = SearchTool()
        # Ensure leads.csv is found relative to the script
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.leads_file = os.path.join(self.base_dir, "leads.csv")
        self.sectors = ["CICD_AI", "MLOPS_INFRA", "ML_RESEARCH"]

    def _get_existing_urls(self) -> Set[str]:
        """Prevents duplicate leads by checking existing URLs."""
        urls = set()
        if os.path.exists(self.leads_file):
            with open(self.leads_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    urls.add(row["URL"].lower().strip("/"))
        return urls

    def generate(self, batch_size: int = 10, focus: str = None):
        """Generates high-signal leads using Gemini and Search."""
        existing_urls = self._get_existing_urls()
        
        print(f"[*] Scouting for {batch_size} new leads...")
        if focus:
            print(f"[*] Focus Area: {focus}")
            search_query = f"top high-growth {focus} AI startups 2024 2025"
        else:
            search_query = "top high-growth AI infrastructure startups MLOps CICD 2025"

        # 1. Real-world context gathering
        print("[*] Gathering market intelligence via Search...")
        snippets = self.search_tool.search(search_query)

        # 2. Gemini-driven synthesis
        prompt = f"""
        Act as an elite tech headhunter specializing in AI Infrastructure.
        Find {batch_size} REAL, high-growth AI startups that are NOT in this list of existing URLs: {list(existing_urls)[:50]}...
        
        Focus areas: MLOps, CI/CD, Vector DBs, AI Observability, and LLM Research.
        
        MARKET CONTEXT (from latest search):
        {snippets}
        
        Return the leads in EXACTLY this CSV format:
        Company Name,URL,Sector
        
        Sectors must be one of: {self.sectors}
        
        Rules:
        - Return ONLY the CSV data.
        - No markdown formatting.
        - Ensure URLs are valid homepages.
        - Be highly selective—only target companies doing deep technical work.
        """

        response = self.llm.invoke(prompt)
        csv_data = response.content.strip()
        
        # 3. Parsing and saving
        lines = csv_data.split('\n')
        added = 0
        
        file_exists = os.path.exists(self.leads_file)
        
        with open(self.leads_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Company Name", "URL", "Email", "Sector"]) # Standardized header
            
            for line in lines:
                if "Company Name" in line or not line.strip():
                    continue
                
                parts = [p.strip(' "') for p in line.split(',')]
                if len(parts) >= 3:
                    name, url, sector = parts[0], parts[1], parts[2]
                    clean_url = url.lower().strip("/")
                    
                    if clean_url not in existing_urls:
                        # Email is left blank—LeadIntelAgent will find it dynamically!
                        writer.writerow([name, url, "", sector])
                        existing_urls.add(clean_url)
                        added += 1
        
        print(f"[+] Successfully added {added} high-signal leads to {self.leads_file}!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate high-signal AI leads.")
    parser.add_argument("--batch", type=int, default=10, help="Number of leads to generate")
    parser.add_argument("--focus", type=str, help="Specific sector focus")
    args = parser.parse_args()

    generator = LeadGenerator()
    generator.generate(batch_size=args.batch, focus=args.focus)
