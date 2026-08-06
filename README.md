# 🏢 AgentOffice

A multi-agent personal automation system with an **isometric virtual office UI**. Your AI agents sit at their desks and walk to your cabin when you summon them - just like a real office!

![AgentOffice Banner](https://img.shields.io/badge/AgentOffice-v0.1.0-blue) ![Python](https://img.shields.io/badge/Python-3.9+-green) ![React](https://img.shields.io/badge/React-18-61DAFB) ![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 🤖 AI Agents
| Agent | Description |
|-------|-------------|
| 📧 **Email Agent** | Scans Gmail, extracts tasks, creates actionable items |
| 🔍 **Tab Monitor** | Tracks AI training platforms (Outlier, Scale AI, Remotasks) |
| 💼 **Freelance Hunter** | Finds jobs on Upwork/Freelancer/Fiverr, drafts proposals |
| 📊 **Status Tracker** | Daily productivity reports and metrics |

### 🎮 Unique Virtual Office UI
- **Isometric 3D office** with your personal cabin
- **Animated agent characters** that walk and talk
- **Interactive chat** - Click an agent, give orders via text
- **Real-time updates** via WebSocket
- **Boss cabin** with your name on it!

### 📱 Multiple Interfaces
- **Web Dashboard** - 3D office + task management panel
- **Telegram Bot** - Mobile control with inline keyboards

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Google Cloud account (for Gmail API)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/agent-office.git
cd agent-office

# Backend setup
pip install -e .
playwright install chromium

# Frontend setup
cd frontend
npm install
cd ..

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Gmail Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create/select a project
3. Enable **Gmail API**
4. Create **OAuth 2.0 credentials** (Desktop app)
5. Download as `credentials.json` in project root
6. Run once to complete OAuth: `python -c "from agents.email_agent import EmailAgent; import asyncio; asyncio.run(EmailAgent().execute())"`

### Running

```bash
# Terminal 1: Backend
uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Telegram Bot (optional)
python -m bot.telegram_bot
```

Open **http://localhost:3000** and enjoy your virtual office! 🎉

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/agents` | GET | List all agents |
| `/agents/{name}/execute` | POST | Run an agent |
| `/tasks` | GET | List all tasks |
| `/tasks/{id}` | PATCH | Update task status |
| `/tasks/approve/{id}` | PATCH | Approve job proposal |
| `/stats` | GET | Token usage stats |
| `/ws` | WebSocket | Real-time updates |

## 🤖 Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Show main menu |
| `/commands` | List all commands |
| `/status` | Agent status overview |
| `/email` | Check Gmail inbox |
| `/platforms` | Check AI training platforms |
| `/jobs [query]` | Search freelance jobs |
| `/report` | Daily productivity report |
| `/pending` | View pending proposals |
| `/approve <id>` | Approve job application |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  3D Office  │  │  Task Panel │  │  Chat Modal │     │
│  │  (Three.js) │  │             │  │             │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
└─────────┼────────────────┼────────────────┼─────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend + WebSocket                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Orchestrator│  │  LLM Client │  │   Database  │     │
│  │             │  │  (Claude)   │  │  (SQLite)   │     │
│  └──────┬──────┘  └─────────────┘  └─────────────┘     │
└─────────┼───────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│                       Agents                             │
│  ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌─────────┐ │
│  │  Email   │ │Tab Monitor│ │  Freelance │ │ Status  │ │
│  │  Agent   │ │   Agent   │ │   Hunter   │ │ Tracker │ │
│  └────┬─────┘ └─────┬─────┘ └──────┬─────┘ └────┬────┘ │
└───────┼─────────────┼──────────────┼────────────┼───────┘
        │             │              │            │
        ▼             ▼              ▼            ▼
    Gmail API    Playwright     Playwright    Database
```

## 💰 Token Efficiency

AgentOffice is designed to minimize LLM token usage:

- **Local preprocessing** - Regex/rules filter before LLM calls
- **Response caching** - Hash-based cache with configurable TTL
- **Structured outputs** - JSON mode for precise responses
- **Tiered models** - Sonnet for simple, Opus for complex tasks

## 🐳 Docker Deployment

```bash
# Build and run all services
docker-compose up -d

# Or build individually
docker build -t agent-office-backend .
docker build -t agent-office-frontend ./frontend
```

## 🔧 Environment Variables

See [.env.example](.env.example) for all configuration options.

**Required:**
- `ANTHROPIC_API_KEY` - For LLM features
- `TELEGRAM_BOT_TOKEN` - For Telegram bot
- `GOOGLE_CREDENTIALS_PATH` - For Gmail integration

## 📁 Project Structure

```
agent-office/
├── api/              # FastAPI backend
├── agents/           # AI agents
├── bot/              # Telegram bot
├── core/             # Shared utilities
├── frontend/         # React + Three.js UI
├── tests/            # Test files
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 👨‍💻 Author

**Mohit Dubey** - Building AI-powered automation tools

---

⭐ Star this repo if you find it useful!
