import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

import csv
import torch
import smtplib
from bs4 import BeautifulSoup
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from dotenv import load_dotenv

# 1. Import modules
from scrapers.startup_hunter import run_discovery
from scrapers.enrichment import find_best_email
from scrapers.email_discovery import extract_domain
from processor.sent_db import init_db, already_contacted, already_contacted_domain, record_sent

load_dotenv()

# --- Configuration ---
# TEST_MODE = True: Always sends the pitch to YOUR email (GMAIL_ADDRESS).
# TEST_MODE = False: Sends the pitch to the actual found lead (USE WITH CAUTION!).
TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
ADAPTER_PATH = os.path.join(BASE_DIR, "my-b2b-adapter")

# --- Limits ---
MAX_MAILS_PER_RUN = 5

# --- Helper Function: The Email Sender ---
def send_cold_email(target_email, startup_name, category):
    my_email = os.getenv("GMAIL_ADDRESS")
    my_password = os.getenv("GMAIL_PASSWORD")
    
    if not my_email or not my_password:
        print("❌ Error: GMAIL_ADDRESS or GMAIL_PASSWORD not found in environment!")
        return

    # In Test Mode, we override the recipient
    recipient = my_email if TEST_MODE else target_email
    
    print(f"📧 Drafting pitch for {startup_name} (Recipient: {recipient})...")
    msg = MIMEMultipart()
    msg['From'] = my_email
    msg['To'] = recipient
    msg['Subject'] = f"Helping {startup_name} scale your engineering team"
    
    body = f"""Hi Team at {startup_name},
    
I noticed your recent update regarding your {category.lower()} and saw you are looking to scale.

To be completely transparent, I actually built a custom autonomous AI agent running a fine-tuned LoRA model on my local GPU specifically to scrape the web, read startup blogs, and find high-growth companies like yours to send this email to. 

I'm Agrim, a first-year ECE student at NSUT specializing in applied AI and agentic frameworks. I'm looking for a remote internship this summer where I can ship code fast. 

Beyond this autonomous outreach engine, my recent projects include:
- A multi-agent CI/CD pipeline diagnostic system using LangGraph and XGBoost.
- A computer vision-powered Vintage Appraiser for identifying and valuing rare collectibles.
- An MCP-based localized productivity server.

You can check out the source code for this email agent and my other work here:
💻 GitHub: [jainagrim297-art]
📄 Resume: [https://drive.google.com/file/d/1s2gCJGrj5PLdVXW2ICQBxRBtDrfA8LsL/view?usp=drivesdk]

If you're open to bringing on a hungry engineer to help build out your infrastructure, I'd love to chat for 5 minutes next week. 

Best,
Agrim Jain
"""
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
        server.login(my_email, my_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Success! Pitch sent to {recipient}.")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

# --- Helper Function: The Text Extractor ---
def scrape_website_text(url):
    """A quick function to read the raw text from the startup's website."""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        text = " ".join([p.get_text() for p in paragraphs])
        return text[:1500] 
    except Exception as e:
        print(f"⚠️ Could not read {url}: {e}")
        return ""

def run_agent():
    print("========================================")
    print("🚀 INITIATING AUTONOMOUS OUTREACH AGENT")
    if TEST_MODE:
        print("⚠️  RUNNING IN TEST MODE (Emails will be sent to yourself)")
    print("========================================\n")

    # Initialize the sent emails database
    init_db()

    # --- Phase 1: Hunt ---
    run_discovery()

    # --- Phase 2: Load Brain ---
    print("\n🧠 Waking up RTX 4060 and loading custom LoRA adapter...")
    base_model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"💻 Using device: {device}")

    try:
        model = AutoModelForCausalLM.from_pretrained(
            base_model_name, 
            device_map={"": device}, 
            torch_dtype=torch.float16 if device == "cuda" else torch.float32
        )
        tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        
        # Consistent pathing for adapter
        if os.path.exists(ADAPTER_PATH):
            model = PeftModel.from_pretrained(model, ADAPTER_PATH)
            print("⚡ AI Engine Online with LoRA adapter.")
        else:
            print("⚠️ LoRA adapter not found. Falling back to base model classification.")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return

    # --- Phase 3: Execute ---
    target_file = os.path.join(DATA_DIR, "target_leads.csv")

    if os.path.exists(target_file):
        print(f"\n📂 Reading fresh leads from {target_file}...")
        
        with open(target_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            sent_count = 0
            
            for row in reader:
                company = row['Company']
                url = row['URL']
                hn_url = row.get('HN_URL', '')
                
                print(f"\n=======================")
                print(f"🔍 Analyzing: {company}")
                print(f"=======================")
                
                # 1. Scrape the text
                print(f"⛏️  Reading website: {url}")
                blog_text = scrape_website_text(url)
                
                if not blog_text:
                    continue

                # 2. Feed the text to the AI Model
                messages = [
                    {"role": "system", "content": "You are a B2B lead generation engine. Classify the following startup engineering blog snippet into exactly one of these categories: [Engineering Infrastructure Scaling, Hiring and Team Expansion, General Company News]. Respond ONLY with the category name."},
                    {"role": "user", "content": blog_text}
                ]
                
                prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                inputs = tokenizer(prompt, return_tensors="pt").to(device)
                
                outputs = model.generate(**inputs, max_new_tokens=10, temperature=0.1)
                ai_classification = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True).strip()
                
                print(f"🎯 AI Decision: {ai_classification}")
                
                # 3. Trigger Enrichment & Email if it's a match!
                if any(signal in ai_classification for signal in ["Hiring", "Infrastructure Scaling"]):
                    if sent_count >= MAX_MAILS_PER_RUN:
                        print(f"\n🛑 Reached session limit of {MAX_MAILS_PER_RUN} emails. Stopping early to protect reputation.")
                        break
                    
                    # Domain Check: Have we already contacted this startup/domain?
                    domain = extract_domain(url)
                    if already_contacted_domain(domain):
                        print(f"⏭️  Skipping {company}: Already reached out to this domain ({domain}) previously.")
                        continue

                    print("🚀 High-Intent Signal Detected! Enriching lead...")
                    
                    found_email = find_best_email(url, hn_url)
                    
                    if found_email:
                        # Deduplication check: Have we already contacted this person?
                        if already_contacted(found_email):
                            print(f"⏭️  Skipping {found_email}: Already contacted in a previous run.")
                            continue

                        # Send the email and record it if successful
                        if send_cold_email(found_email, company, ai_classification):
                            record_sent(found_email, company, ai_classification, domain=domain)
                            sent_count += 1
                    else:
                        print("⏸️ Could not find a contact email. Skipping email phase.")
                else:
                    print("⏸️ No immediate hiring signal. Skipping email.")
                
    else:
        print("❌ No leads file found. Discovery phase may have failed.")

    print("\n✅ Agent run complete. Shutting down system.")

if __name__ == "__main__":
    run_agent()