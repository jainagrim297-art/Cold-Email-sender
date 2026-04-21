# Structured output schemas (PainPoints, Leads)
from pydantic import BaseModel, Field

class ContactInfo(BaseModel):
    name: str = Field(description="Name of the CEO, Founder, or Hiring Manager. 'Hiring Manager' if unknown.")
    email: str = Field(description="Best email to contact (careers@, jobs@, or personal). Empty string if none.")

class TechnicalInsight(BaseModel):
    pain_point: str = Field(description="Specific engineering bottleneck (e.g., flaky CI tests).")
    evidence: str = Field(description="Direct snippet or evidence from the blog.")
    relevance_score: float = Field(description="Score (0-1) based on your ECE projects.")
    suggested_fix: str = Field(description="How CodeBERT/XGBoost could solve this.")

