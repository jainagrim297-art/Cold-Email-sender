from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.state import AgentState
from pydantic import BaseModel, Field
from typing import List

class LeadIntelOutput(BaseModel):
    company_segment: str = Field(description="One of: CICD_AI | MLOPS_INFRA | ML_RESEARCH")
    suitable_person_name: str
    suitable_person_title: str
    email_pattern: str
    predicted_email: str
    verification_confidence: float

class LeadIntelAgent:
    def __init__(self):
        # Using Gemini 1.5 Pro for its ability to follow complex B2B logic and pattern matching
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.1)

    def generate_queries(self, state: AgentState):
        """Phase 1: Generate high-signal Google Dorks for lead discovery."""
        company_name = state["company_name"]
        # Simple domain extraction from URL
        company_domain = state["target_url"].replace("https://", "").replace("http://", "").split("/")[0]
        
        prompt = f"""
        Act as a Senior B2B Data Architect specializing in Lead Intelligence.
        Generate 3 advanced search queries (Google Dorks) to find the target technical decision-maker (CTO, Head of Eng, or Lead Architect) at {company_name} and their email footprint.

        Target Domain: {company_domain}

        USER PORTFOLIO FOCUS & HOOKS:
        - Segment A (CI/CD): Target DevOps Leads or Engineering Managers. (Hook: CodeBERT/XGBoost Failure Diagnosis)
        - Segment B (MLOps): Target Platform Architects or Head of Infra. (Hook: n8n Workflows/Neural Networks)
        - Segment C (Research): Target Chief Scientists or Research Directors. (Hook: RAG Devices/Adobe Hackathon)

        REQUIRED QUERY FORMATS:
        - Query 1: site:{company_domain} 'engineering' (CTO OR 'VP of Engineering' OR 'Manager')
        - Query 2: {company_name} 'hiring manager' email
        - Query 3: {company_name} '@{company_domain}' -site:{company_domain}

        Return ONLY a list of the 3 generated queries, one per line.
        """
        
        response = self.llm.invoke(prompt)
        queries = [q.strip() for q in response.content.strip().split('\n') if q.strip()]
        
        return {
            "search_queries": queries,
            "history": ["Generated Lead Intelligence search queries (Google Dorks)"]
        }

    def analyze_snippets(self, state: AgentState):
        """Phase 2: Analyze search results to identify the person and email pattern."""
        company_name = state["company_name"]
        company_domain = state["target_url"].replace("https://", "").replace("http://", "").split("/")[0]
        search_snippets = state.get("search_snippets", "No snippets found.")
        segment = state.get("target_segment", "ML_RESEARCH")

        prompt = f"""
        Act as a Senior B2B Data Architect specializing in Lead Intelligence. 
        Your goal is to identify the most 'Suitable Person' (CTO, Head of Engineering, or Lead Architect) at {company_name} and determine their most likely email address based on the provided data.

        CONTEXT:
        Company: {company_name}
        Domain: {company_domain}
        Sector: {segment}

        USER PORTFOLIO FOCUS:
        - Segment A (CI/CD): Target DevOps Leads or Engineering Managers. (Hook: CodeBERT/XGBoost Failure Diagnosis)
        - Segment B (MLOps): Target Platform Architects or Head of Infra. (Hook: n8n Workflows/Neural Networks)
        - Segment C (Research): Target Chief Scientists or Research Directors. (Hook: RAG Devices/Adobe Hackathon)

        STEP 2: EMAIL PATTERN ANALYTICS
        Analyze these search snippets: 
        {search_snippets}

        Identify the company's email convention based on known B2B patterns:
        - f.lastname@{company_domain}
        - first.last@{company_domain}
        - first@{company_domain}

        STEP 3: DECISION MAKER IDENTIFICATION
        Identify the highest-ranking technical decision-maker mentioned in the snippets.

        STEP 4: OUTPUT RULES
        - Provide a structured JSON object.
        - If verification_confidence is low (< 0.5), DO NOT guess a risky email.
        - NEVER include 'N/A' or dummy names in the predicted_email.
        - If no clear pattern is found, return an empty string for predicted_email.
        """
        
        result = self.llm.with_structured_output(LeadIntelOutput).invoke(prompt)
        
        return {
            "lead_intel": result.model_dump(),
            "hiring_manager_name": result.suitable_person_name,
            "hiring_manager_email": result.predicted_email,
            "history": [f"Identified {result.suitable_person_name} ({result.suitable_person_title}) as the target lead."]
        }
