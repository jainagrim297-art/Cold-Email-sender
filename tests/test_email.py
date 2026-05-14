import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from dotenv import load_dotenv

# Let's import the email function you already built
from src.main import send_cold_email

def test_email():
    load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))
    
    my_email = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_PASSWORD")
    
    if not password:
        print("❌ Error: GMAIL_PASSWORD in .env is empty!")
        print("   Please generate a Google App Password and put it in your .env file.")
        return
        
    print(f"📧 Attempting to test SMTP engine for: {my_email}")
    send_cold_email(my_email, "Test Startup Inc.", "Hiring")

if __name__ == "__main__":
    test_email()
