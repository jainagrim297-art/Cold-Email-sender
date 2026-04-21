import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load environment variables
load_dotenv()

print("🚀 Initializing Gemini API via LangChain...")

# We use gemini-1.5-flash because it is lightning fast, cheap, and perfect for classification tasks
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)

# The Prompt Template: This forces Gemini to output strict JSON in the ChatML format
prompt_template = PromptTemplate.from_template(
    """You are an expert AI data labeler. Your job is to take raw startup blog text and convert it into a strict JSON format for fine-tuning.

You must classify the text into exactly ONE of these categories:
- Engineering Infrastructure Scaling
- Hiring and Team Expansion
- General Company News

RAW TEXT:
{raw_text}

OUTPUT INSTRUCTIONS:
Output ONLY a valid JSON object matching exactly this structure, with no markdown formatting, no backticks, and no extra text:
{{"messages": [{{"role": "system", "content": "You are a B2B lead generation engine. Classify the following startup engineering blog snippet into exactly one of these categories: [Engineering Infrastructure Scaling, Hiring and Team Expansion, General Company News]. Respond ONLY with the category name."}}, {{"role": "user", "content": "{raw_text}"}}, {{"role": "assistant", "content": "<INSERT CATEGORY HERE>"}}]}}
"""
)

# Create the LangChain pipeline
chain = prompt_template | llm

# --- Mock Data --- 
scraped_blogs = [
    "We are migrating our entire backend from AWS EC2 to a custom Kubernetes cluster to reduce latency.",
    "Excited to announce that we are looking for 10 new Senior Python Developers to join our remote team!",
    "Our CEO will be speaking at the upcoming TechCrunch Disrupt conference about the future of AI.",
    "Due to hitting 10 million users, our PostgreSQL database crashed, prompting a complete rewrite of our indexing logic.",
    "Welcome to our new office in San Francisco! We had a great time at the launch party with the whole team."
]

print(f"📄 Found {len(scraped_blogs)} scraped blogs. Starting synthetic data generation...\n")

# Open the jsonl file in "append" mode
with open("dataset.jsonl", "a", encoding="utf-8") as f:
    for i, blog in enumerate(scraped_blogs):
        print(f"Processing blog {i+1}/{len(scraped_blogs)}...")
        
        try:
            # Ask Gemini to classify the text and build the JSON
            result = chain.invoke({"raw_text": blog})
            
            # Extract ONLY the text between the first { and the last }
            raw_output = result.content
            start_idx = raw_output.find('{')
            end_idx = raw_output.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                cleaned_result = raw_output[start_idx:end_idx]
                
                # Verify it is mathematically valid JSON before saving it
                json_data = json.loads(cleaned_result)
                
                # Write exactly one perfect line to the training file
                f.write(json.dumps(json_data) + "\n")
            else:
                print(f"❌ Error: Could not find valid JSON brackets in output.")
                print(f"Raw Output was: {raw_output}")
            
        except Exception as e:
            print(f"❌ Error processing blog {i+1}: {e}")
            if 'result' in locals():
                print(f"Raw Output was: {result.content}")

print("\n✅ Synthetic Dataset Generation Complete! Open dataset.jsonl to see your training data.")