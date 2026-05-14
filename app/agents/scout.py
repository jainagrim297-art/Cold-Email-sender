import requests
from bs4 import BeautifulSoup
from app.core.state import AgentState

from app.tools.scraper import WebScraper
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.schema import ContactInfo

class ScoutAgent:
    def __init__(self):
        # High-signal keywords for sector classification
        self.segments = {
            "CICD_AI": ["devops", "ci/cd", "infrastructure", "deployment", "automation"],
            "MLOPS_INFRA": ["observability", "monitoring", "scalability", "vector", "database"],
            "ML_RESEARCH": ["nlp", "llm", "foundation", "generative", "rag", "reasoning"]
        }
        self.scraper = WebScraper()
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.1)

    def _classify_sector(self, description: str) -> str:
        description = description.lower()
        for sector, keywords in self.segments.items():
            if any(word in description for word in keywords):
                return sector
        return "ML_RESEARCH" # Default to research for AI startups

    def run(self, state: AgentState):
        target_url = state.get("target_url") or "https://example.com"
        
        # 1. LIVE SCRAPING: Read the homepage text to understand the startup's product
        print(f"[*] ScoutAgent is crawling {target_url}...")
        website_content = self.scraper.scrape_to_markdown(target_url)
        
        # 1.5 Extract Contact Info using Gemini
        contact_prompt = f"Analyze this website content and extract the name of a founder/CEO or hiring manager, and any contact email. Content: {website_content[:15000]}"
        try:
            contact_info = self.llm.with_structured_output(ContactInfo).invoke(contact_prompt)
            found_name = contact_info.name
            found_email = contact_info.email
        except:
            found_name = "Hiring Manager"
            found_email = ""

        # 2. Classify the sector organically (unless already provided)
        target_segment = state.get("target_segment")
        if not target_segment or target_segment not in self.segments:
            target_segment = self._classify_sector(website_content)
        
        # 3. Predict the blog URL for the Researcher
        blog_url = f"{target_url}/blog"
        
        # Only override email if CSV didn't provide one
        csv_email = state.get("hiring_manager_email", "")
        final_email = csv_email if csv_email else found_email
        
        return {
            "target_segment": target_segment,
            "blog_url": blog_url,
            "hiring_manager_name": found_name,
            "hiring_manager_email": final_email,
            "history": [f"Scraped {target_url}. Sector: {target_segment}. Found contact: {found_name}"]
        }
