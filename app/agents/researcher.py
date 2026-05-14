from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.schema import TechnicalInsight
from app.core.state import AgentState

class ResearcherAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.7)

    def run(self, state: AgentState):
        segment = state.get("target_segment", "")
        content = state.get("raw_blog_data", "")
        
        # Select prompt based on your completed courses (ML, Deep Learning, NLP)
        if segment == "CICD_AI":
            prompt = f"Find flakiness in their build logs or CI bottlenecks. Use my CodeBERT/XGBoost expertise as the solution hook. Context: {content}"
        elif segment == "MLOPS_INFRA":
            prompt = f"Find challenges in model monitoring, drift, or deployment latency. Use my Neural Network/Deep Learning background as the hook. Context: {content}"
        else: # ML_RESEARCH
            prompt = f"Analyze their latest paper or technical deep-dive. Identify a potential extension or benchmark. Use my NLP/LangChain background as the hook. Context: {content}"

        insight = self.llm.with_structured_output(TechnicalInsight).invoke(prompt)
        return {
            "technical_audit": [insight.model_dump()],
            "history": [f"Researched {segment}"]
        }