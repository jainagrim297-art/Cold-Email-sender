from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime

class RawSignal(BaseModel):
    """The initial data captured from the web."""
    title: str
    url: str
    raw_html: str
    source: str
    timestamp: datetime = Field(default_factory=datetime.now)

class CleanedSignal(BaseModel):
    """The signal after stripping HTML and extracting the core text."""
    title: str
    url: str
    cleaned_text: str
    source: str
    # Helps track if we already processed this
    fingerprint: str 

class SignalAnalysis(BaseModel):
    """The result of the NLP classification."""
    category: str  # e.g., "Funding", "Tech Migration", "Hiring"
    relevance_score: float = Field(ge=0.0, le=1.0) # Must be between 0 and 1
    key_pain_points: List[str] = []
    is_actionable: bool = False

class FinalLead(BaseModel):
    """The complete 'Lead' object ready for outreach."""
    signal: CleanedSignal
    analysis: SignalAnalysis
    company_name: Optional[str] = None
    contact_email: Optional[str] = None
    outreach_status: str = "pending" # pending, drafted, sent