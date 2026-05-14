from typing import TypedDict, List, Annotated, Optional, Literal
from operator import add

# Define the three sectors you are focusing on
Sector = Literal["CICD_AI", "MLOPS_INFRA", "ML_RESEARCH"]

class AgentState(TypedDict):
    # Discovery Meta
    company_name: str
    target_url: str
    target_segment: Sector # Critical: Routes the reasoning logic
    
    # Audit trail
    technical_audit: Annotated[List[dict], add]
    
    # Skills alignment (Deep context from your background)
    portfolio_match: dict 
    
    # Lead Intelligence (New)
    search_queries: Optional[List[str]]
    search_snippets: Optional[str]
    lead_intel: Optional[dict]
    
    # Final Communication
    email_draft: str
    hiring_manager_email: str
    hiring_manager_name: str
    email_sent_status: str
    history: Annotated[List[str], add]