import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import google.generativeai as genai
from dotenv import load_dotenv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Load your API key from the .env file
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("🔍 Checking which Gemini models your API key has access to...\n")

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            # We strip out the "models/" part so you can easily copy-paste it
            clean_name = model.name.replace('models/', '')
            print(f"✅ Available Model Name: {clean_name}")
except Exception as e:
    print(f"❌ Error connecting to Google: {e}")