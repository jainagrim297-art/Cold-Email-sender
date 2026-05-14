import smtplib
from email.mime.text import MIMEText
import os

class GmailSender:
    def __init__(self):
        self.email = os.getenv("GMAIL_ADDRESS", "your_email@gmail.com")
        self.password = os.getenv("GMAIL_APP_PASSWORD", "your_app_password_here").replace(" ", "")

    def send_email(self, to_email: str, subject: str, company: str, body: str) -> bool:
        # Simulation lock to prevent crashes if the user hasn't set their configuration
        if self.password == "your_app_password_here" or not self.password:
            print(f"\n[*] (SIMULATION) Would send email to: {to_email}")
            print(f"[*] (SIMULATION) Subject: {subject}")
            return True

        # Real sending mode
        msg = MIMEText(body.encode('ascii', 'ignore').decode('ascii'))
        msg['Subject'] = subject
        msg['From'] = self.email
        msg['To'] = to_email

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email, self.password)
                server.send_message(msg)
            print(f"[*] (SUCCESS) Email delivered to {to_email}!")
            return True
        except Exception as e:
            print(f"[*] (ERROR) SMTP Error: {e}")
            return False
