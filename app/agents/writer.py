from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.state import AgentState

class WriterAgent:
    def __init__(self):
        # Leveraging Gemini 1.5 Pro for nuanced persona writing
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0.7)

    def run(self, state: AgentState):
        segment = state["target_segment"]
        audit = state["technical_audit"][-1]
        
        # Sector-specific portfolio highlighting logic
        if segment == "CICD_AI":
            portfolio_hook = "automated CI/CD failure diagnosis using CodeBERT and XGBoost."
            value_prop = "automating the classification of root causes in your build logs."
        elif segment == "MLOPS_INFRA":
            portfolio_hook = "automated data pipelines and observability using n8n and Neural Networks."
            value_prop = "optimizing model deployment latencies and automated re-training workflows."
        else: # ML_RESEARCH
            portfolio_hook = "custom RAG devices and a GenAI Brand Health Checker for an Adobe hackathon."
            value_prop = "extending your latest research on context graphs or RAG reliability."

        target_name = state.get("hiring_manager_name", "Hiring Manager")
        if target_name.lower() in ["unknown", "hiring manager", ""]:
            target_name = "Hiring Manager"

        prompt = f"""
        Act as a highly confident, technically elite 1st-year ECE student at NSUT (Netaji Subhas University of Technology), New Delhi. 
        Your name is Agrim Jain. You are an 'Obsessive Builder'—proud of your work and deeply impressed (glazing) by their engineering.

        Target Company: {state['company_name']}
        Target Name: {target_name}
        Sector: {segment}
        Company Pain Point: {audit['pain_point']}
        
        Structure the email as follows:
        1. The Hook (Glazing): Start with a confident, high-energy compliment about their recent work on {audit['pain_point']}. Mention that you are genuinely obsessed with how they've structured their {segment} stack.
        2. The Meta Flex: Reveal that you are a 1st-year student at NSUT New Delhi and that you built this entire agentic discovery and outreach swarm autonomously to find 'high-signal' teams like theirs.
        3. Technical Proof (Confident): Explain your CodeBERT + XGBoost diagnostic tool for build logs. Don't just list it—frame it as a sophisticated solution to the bottlenecks they face.
        4. Portfolio & Hackathons: Mention your Brand Health Checker (Adobe Hackathon winner/top-tier) and custom RAG devices as proof of your speed and technical depth.
        5. The Ask: Ask for a quick technical sync or a review of your GitHub (https://github.com/jainagrim297-art). State that you are looking for a team that matches your "obsessive building" energy.
        
        Tone: Confident, ambitious, technical, and impressive. Show them that despite being a 1st-year student, your output rivals senior engineers. Stay under 160 words.
        
        Sign off with:
        Best regards,
        Agrim Jain 
        1st Year, ECE @ NSUT New Delhi
        GitHub: https://github.com/jainagrim297-art
        """
        
        email = self.llm.invoke(prompt)
        return {
            "email_draft": email.content,
            "history": [f"Drafted email for {segment}"]
        }