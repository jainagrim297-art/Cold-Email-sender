import os
import sqlite3
import time
import sys
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver 

# Ensure leads.csv is found relative to the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEADS_PATH = os.path.join(BASE_DIR, "leads.csv")
DB_PATH = os.path.join(BASE_DIR, "internship_hunt.db")

# --- LOCAL IMPORTS ---
from state import AgentState
from agents.scout import ScoutAgent
from agents.researcher import ResearcherAgent
from agents.writer import WriterAgent
from agents.lead_intelligence import LeadIntelAgent
from tools.search import SearchTool
from agents.sender import SenderAgent

load_dotenv()

# 1. Initialize Persistence
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
memory = SqliteSaver(conn)

def build_workflow():
    builder = StateGraph(AgentState)

    lead_intel = LeadIntelAgent()
    search_tool = SearchTool()

    builder.add_node("scout", ScoutAgent().run)
    builder.add_node("lead_intel_query", lead_intel.generate_queries)
    
    def run_search(state: AgentState):
        snippets = search_tool.run_multi_search(state["search_queries"])
        return {"search_snippets": snippets, "history": ["Performed web search for lead intelligence"]}
    
    builder.add_node("search", run_search)
    builder.add_node("lead_intel_analyze", lead_intel.analyze_snippets)
    builder.add_node("researcher", ResearcherAgent().run)
    builder.add_node("writer", WriterAgent().run)
    builder.add_node("sender", SenderAgent().run)

    builder.add_edge(START, "scout")
    
    def check_scout(state: AgentState):
        if state.get("target_url"):
            return "lead_intel_query"
        return END

    builder.add_conditional_edges("scout", check_scout)
    builder.add_edge("lead_intel_query", "search")
    builder.add_edge("search", "lead_intel_analyze")
    builder.add_edge("lead_intel_analyze", "researcher")
    builder.add_edge("researcher", "writer")
    
    # Conditional send logic
    def check_email(state: AgentState):
        if state.get("hiring_manager_email"):
            return "sender"
        return END

    builder.add_conditional_edges("writer", check_email)
    builder.add_edge("sender", END)

    # Completely autonomous execution, uninterrupted
    return builder.compile(checkpointer=memory)

import csv

if __name__ == "__main__":
    graph = build_workflow()
    
    print("Launching specialized hunt from leads.csv...")
    
    if not os.path.exists(LEADS_PATH):
        print(f"[*] (CRITICAL) Could not find: {LEADS_PATH}")
        sys.exit(1)

    with open(LEADS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            company_name = row["Company Name"]
            target_url = row["URL"]
            hiring_email = row.get("Email", "")
            target_sector = row.get("Sector", "")
            
            # thread_id separates runs. We append time to force a fresh run instead of resuming the old failed one!
            config = {"configurable": {"thread_id": f"hunt_run_{idx}_{int(time.time())}"}}
            
            print(f"\n======================================")
            print(f"Target: {company_name} | Email: {hiring_email} | Sector: {target_sector}")
            print(f"======================================")

            initial_input = {
                "company_name": company_name,
                "target_url": target_url,
                "target_segment": target_sector,
                "hiring_manager_email": hiring_email,
                "hiring_manager_name": "",
                "history": [] 
            }

            for event in graph.stream(initial_input, config, stream_mode="values"):
                if "history" in event and event["history"]:
                    print(f"Current Audit: {event['history'][-1]}")

            print("======================================\n")
