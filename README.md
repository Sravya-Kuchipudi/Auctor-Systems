# Auctor Systems — Autonomous Multi-Agent Website Generation Platform

Auctor Systems is an end-to-end, multi-agent AI software studio for autonomous website design, engineering, QA, documentation, and deployment. It coordinates 8 specialized agents, a real-time event streaming pipeline, human-in-the-loop clarification, automated QA defect-revision loops, and continuous live preview updates.

---

## 🏛️ The 8-Agent Autonomous Studio

The platform orchestrates 8 specialized autonomous agents in a deterministic pipeline:

1. **Victoria Vance (Planning & Architecture)**: Analyzes project directives, creates milestone schedules, and formulates architectural blueprints.
2. **Beatrice Stone (Requirements Analyst)**: Gathers functional requirements, identifies ambiguities, and drives human clarification dialogs.
3. **Clara Delacroix (Design Director)**: Produces the design system tokens, typography hierarchy, layouts, and color palettes.
4. **Maya Thorne (Lead Fullstack Developer)**: Implements production-ready code, components, state management, and file systems.
5. **Astrid Lindqvist (QA & Test Automation)**: Runs test suites, identifies defects, and drives iterative defect-fix loops with Maya.
6. **Genevieve Ward (Technical Documentation)**: Produces documentation, API specifications, and architecture guides.
7. **Nadia Chen (DevOps & Infrastructure)**: Generates deployment manifests, builds container configurations, and coordinates deployment.
8. **Sophia Laurent (Marketing & Launch Strategist)**: Crafts go-to-market copy, SEO metadata, release notes, and launch announcements.

---

## 📁 Repository Structure

```text
├── backend/
│   ├── agents/               # Agent definitions and system prompts
│   ├── orchestrator/         # Workflow engine, base agent, event types, state registry
│   ├── services/             # LLM provider, disk file storage, deployment services
│   ├── config.py             # Central environment and runtime configuration
│   ├── database.py           # SQLite persistence layer with transactions
│   ├── main.py               # FastAPI application with REST & SSE endpoints
│   ├── models.py             # Pydantic schemas and domain models
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Sample environment variables template
├── frontend/
│   ├── src/                  # React components, Living Office, Activity Feed, Preview
│   ├── package.json          # Node dependencies and scripts
│   └── vite.config.js        # Vite build configuration
├── walkthrough.md            # Phase 3A Architecture & Conversation Engine Walkthrough
├── walkthrough_phase3b.md    # Phase 3B Backend Integration & QA Engine Walkthrough
└── .gitignore                # Git exclusions (credentials, databases, build artifacts)
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Google Gemini API Key**

### 1. Backend Setup

```bash
cd backend
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Configure your `.env` file with your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini/gemini-2.5-flash
PORT=8000
```

Start the FastAPI backend:
```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The application will be accessible at `http://localhost:5173`.

---

## 🛡️ Security Note

Never commit `.env` or sensitive API keys to version control. The repository includes pre-configured `.gitignore` rules that protect credentials and runtime databases.
