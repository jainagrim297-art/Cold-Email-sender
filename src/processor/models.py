from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta

class RawSignal(BaseModel):
    title: str
    url: str
    raw_html: str
    source: str
    published_at: Optional[datetime] = None
    scraped_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_recent(self) -> bool:
        # If we can't find a date, we assume it's new to be safe
        if not self.published_at:
            return True 
        
        # Define "Recent" as within the last 30 days
        return datetime.now() - self.published_at < timedelta(days=30)