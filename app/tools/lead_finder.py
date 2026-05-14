import os
import csv
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def generate_leads(batch_size=50):
    print(f"[*] Asking Gemini to scout {batch_size} high-growth AI startups...")
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.7)
    
    prompt = f"""
    Act as an elite tech headhunter. 
    Find {batch_size} REAL, high-growth AI startups (focus on MLOps, CI/CD, Vector DBs, or AI Infrastructure).
    Return ONLY a valid CSV format with the exact following columns:
    Company Name,URL,Email
    
    For the email, guess the most likely career or founder contact format (e.g., founders@company.com, careers@).
    Do not include markdown backticks (```csv ... ```). Just the raw CSV text.
    """
    
    try:
        response = llm.invoke(prompt)
        csv_content = response.content.replace("```csv", "").replace("```", "").strip()
        
        # Append to leads.csv
        lines = csv_content.split('\n')
        added = 0
        
        with open("leads.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for line in lines:
                if "Company Name" in line:
                    continue # Skip header
                if line.strip():
                    row = [x.strip(' "') for x in line.split(',')]
                    if len(row) == 3:
                        writer.writerow(row)
                        added += 1
                        
        print(f"[*] Successfully appended {added} new leads to leads.csv!")
    except Exception as e:
        print(f"[*] Error generating leads: {e}")

if __name__ == "__main__":
    generate_leads()
