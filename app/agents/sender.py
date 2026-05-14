from app.tools.mailer import GmailSender
from app.core.state import AgentState

class SenderAgent:
    def __init__(self):
        self.mailer = GmailSender()

    def run(self, state: AgentState):
        draft = state.get("email_draft", "")
        company = state.get("company_name", "Startup")
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        to_email = state.get("hiring_manager_email", "")
        if not to_email or not re.match(email_regex, to_email) or "example.com" in to_email:
            return {
                "email_sent_status": "Skipped",
                "history": [f"Skipped invalid/placeholder email: {to_email}"]
            }

        # Extract subject from draft (assuming format "Subject: ...\n\nDear...")
        lines = draft.split("\n")
        subject = f"Intro: {company} | Agrim Jain"
        for line in lines:
            if line.startswith("Subject:"):
                subject = line.replace("Subject:", "").strip()
                break

        success = self.mailer.send_email(to_email, subject, company, draft)
        status = "Sent" if success else "Failed"
        return {
            "email_sent_status": status, 
            "history": [f"Attempted email delivery to {to_email}. Status: {status}"]
        }
