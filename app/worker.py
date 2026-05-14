import os
import json
import time
import redis
from dotenv import load_dotenv

# Absolute imports
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app.main import build_workflow

load_dotenv()

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_QUEUE = "outreach_tasks"

def run_worker():
    """
    Background worker that consumes leads from Redis and runs the LangGraph pipeline.
    """
    print(f"[*] Worker started. Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}...")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    graph = build_workflow()

    while True:
        try:
            # BLPOP blocks until a task is available in the queue
            _, task_data = r.blpop(REDIS_QUEUE)
            lead = json.loads(task_data)
            
            company_name = lead.get("company_name")
            target_url = lead.get("target_url")
            hiring_email = lead.get("hiring_manager_email", "")
            
            print(f"\n[⚡ WORKER] Processing lead: {company_name}...")
            
            # Run the LangGraph pipeline
            config = {"configurable": {"thread_id": f"worker_run_{int(time.time())}"}}
            initial_input = {
                "company_name": company_name,
                "target_url": target_url,
                "hiring_manager_email": hiring_email,
                "hiring_manager_name": "",
                "history": [] 
            }
            
            # Execute the graph
            result = graph.invoke(initial_input, config=config)
            
            status = result.get("email_sent_status", "Unknown")
            print(f"[✅ WORKER] Completed {company_name}. Status: {status}")
            
        except Exception as e:
            print(f"[❌ WORKER ERR] Error processing task: {e}")
            time.sleep(2) # Prevent rapid-fire errors

if __name__ == "__main__":
    run_worker()
