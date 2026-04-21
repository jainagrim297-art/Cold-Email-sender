from fastapi import FastAPI
from pydantic import BaseModel
import time

# Import your incredibly powerful LangGraph pipeline and State
from main import build_workflow

app = FastAPI(title="Outreach AI Agent Backend", version="1.0.0")

# Build the swarm engine once on startup
graph = build_workflow()

class LeadRequest(BaseModel):
    company_name: str
    target_url: str
    hiring_manager_email: str

import redis
import json

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_QUEUE = "outreach_tasks"
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

@app.post("/api/v1/outreach/enqueue")
async def enqueue_outreach_task(lead: LeadRequest):
    """
    FastAPI Producer: Pushes a lead into the Redis queue for asynchronous parallel processing.
    """
    print(f"\n[📥 API RECEIVED] Enqueuing lead: {lead.company_name}...")
    
    task_payload = {
        "company_name": lead.company_name,
        "target_url": lead.target_url,
        "hiring_manager_email": lead.hiring_manager_email
    }
    
    # Push to Redis
    r.rpush(REDIS_QUEUE, json.dumps(task_payload))
    
    return {
        "status": "enqueued",
        "target_company": lead.company_name,
        "message": "Task received and added to the parallel processing queue."
    }

@app.post("/api/v1/outreach/generate_sync")
async def trigger_langgraph_sync(lead: LeadRequest):
    """
    Synchronous execution (original behavior) for direct API testing.
    """
    print(f"\n[🚀 API SYNC] Launching swarm on: {lead.company_name}...")
    config = {"configurable": {"thread_id": f"api_sync_{int(time.time())}"}}
    initial_input = {
        "company_name": lead.company_name,
        "target_url": lead.target_url,
        "hiring_manager_email": lead.hiring_manager_email,
        "hiring_manager_name": "",
        "history": [] 
    }
    return graph.invoke(initial_input, config=config)


@app.get("/health")
def health_check():
    return {"status": "Agentic Swarm is Online and Ready to hunt."}
