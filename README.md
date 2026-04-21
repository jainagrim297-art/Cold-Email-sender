# AI Outreach Agent Swarm 🚀

An autonomous, multi-agent system designed for hyper-personalized startup outreach. Built with **LangGraph**, **Gemini 1.5 Pro**, **Apollo.io**, and **Hunter.io**.

## 🌟 Key Features

- **Pro Lead Discovery**: Fetch high-signal technical decision-makers (Founders, CTOs) directly via Apollo.io.
- **Double Verification**: Guaranteed zero bounce rates with Hunter.io email validation.
- **Autonomous Research**: Specialized agents crawl company websites and blogs to find deep technical hooks.
- **Hyper-Personalized Drafting**: Tailors every email to the recipient's specific engineering bottlenecks and your unique portfolio.
- **Human-in-the-Loop**: Interactive CLI review panel to approve, edit, or skip drafts before sending.
- **Massive Scaling**: Asynchronous parallel processing pipeline powered by Docker, Redis, and FastAPI.

## 🛠️ Project Structure

```text
intern_agent/
├── agents/             # Core AI reasoning logic
│   ├── scout.py        # Crawls & classifies startups
│   ├── researcher.py   # Finds technical hooks
│   ├── writer.py       # Drafts personalized emails
│   └── sender.py       # Handles Gmail delivery
├── tools/              # API & Technical integrations
│   ├── lead_intelligence_pro.py  # Apollo + Hunter Logic
│   ├── search.py       # Web search fallback
│   └── scraper.py      # AI-powered web scraping
├── outreach_bot.py     # Main Interactive CLI
├── api.py              # FastAPI Producer
├── worker.py           # Redis Consumer (Parallel Worker)
├── docker-compose.yml  # Scaling infrastructure
└── leads.csv           # Local lead database
```

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+
- Docker & Docker Compose (for parallel mode)
- Google AI Studio (Gemini), Apollo.io, and Hunter.io API keys.

### 2. Setup
```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure environment
cp .env.example .env  # Add your keys here
```

### 3. Running the Bot

#### A. Interactive CLI Mode (Best for Quality Control)
Process leads one-by-one with a review step.
```bash
# Use Apollo to find new leads
python outreach_bot.py --source apollo

# Use your local leads.csv
python outreach_bot.py --source csv
```

#### B. Parallel "Swarm" Mode (Best for Volume)
Scale to multiple workers using Docker and Redis.
```bash
docker compose up --build --scale worker=3
```

## 📬 API Endpoints

- **POST `/api/v1/outreach/enqueue`**: Pushes a lead into the Redis queue for the swarm to process.
- **GET `/health`**: Check system status.

---
*Built for Agrim Jain's Internship Hunt 2026. Powered by Advanced Agentic Coding.*
