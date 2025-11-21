# 🚀 Telecom AI Multi-Agent System - Phase 0

**Version:** 0.1.0  
**Status:** Production-Ready Infrastructure  
**Phase:** Phase 0 (Core Foundation)

---

## 📋 Overview

A fully local, offline AI multi-agent system for telecommunications operators. Built for on-premises deployment with zero cloud dependency.

**Key Features:**
- ✅ Local-first architecture (all data stays on-premises)
- ✅ Multi-agent orchestration (Correlation, Forecasting, Anomaly detection)
- ✅ Task queue management (FIFO serialized execution)
- ✅ SQLite database persistence
- ✅ Web-based frontend (vanilla JavaScript)
- ✅ Safety & security guardrails
- ✅ Prepared for LLM integration (Phase 1)

---

## 🏗️ Architecture

### System Layers

```
┌─────────────────────────────────────┐
│   User Interface (Web Browser)      │  ← Frontend: index.html + app.js
├─────────────────────────────────────┤
│   API Server (FastAPI :8000)        │  ← REST endpoints
├─────────────────────────────────────┤
│   Orchestrator (Task Management)    │  ← Task queue + agent routing
├─────────────────────────────────────┤
│   Agents (Base + Specialized)       │  ← Multi-agent execution
├─────────────────────────────────────┤
│   Support Modules                   │  ← DB, Memory, Safety, LLM Config
└─────────────────────────────────────┘
```

### Module Breakdown

| Module | Purpose | Files |
|--------|---------|-------|
| **orchestrator** | Agent coordination & task routing | 6 files |
| **memory** | In-memory cache + persistence | 3 files |
| **trust_safety** | Input validation & security | 3 files |
| **database** | SQLite CRUD operations | 2 files |
| **API Server** | FastAPI REST endpoints | 1 file |
| **Frontend** | Web UI (HTML + JS + CSS) | 3 files |

---

## 🔧 Setup Instructions

### Prerequisites

- **Python 3.10+** (recommended: 3.11)
- **Git** (for version control)
- **pip** (Python package manager)
- **Intel Core i7-8750H or equivalent** (optimized for this spec)
- **32GB RAM** (recommended)
- **Windows, macOS, or Linux**

### Installation Steps

#### 1. Clone or Download Project

```bash
# Create project directory
mkdir ai-agent-system
cd ai-agent-system

# Copy all Phase 0 files into this directory
# (Files provided separately)
```

#### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Create Data Directories

```bash
mkdir data logs data/uploads
```

#### 5. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env if needed (defaults work for Phase 0)
```

#### 6. Initialize Database

Database auto-initializes on first API startup.

#### 7. Start API Server

```bash
python api_server.py
```

**Expected Output:**
```
2025-11-21 10:55:00 - root - INFO - Starting API server on 127.0.0.1:8000
...
✅ Application startup complete
Uvicorn running on http://127.0.0.1:8000
```

#### 8. Access Frontend

Open browser: **http://127.0.0.1:8000**

---

## 📊 Project Structure

```
ai-agent-system/
├── orchestrator/                  # Agent coordination
│   ├── __init__.py
│   ├── base_agent.py             # Abstract base class
│   ├── agent_registry.py         # Agent registration
│   ├── task_manager.py           # Task queue (FIFO)
│   ├── orchestrator.py           # Main coordinator
│   └── llm_config.py             # LLM config (Phase 1)
│
├── memory/                        # Caching & persistence
│   ├── __init__.py
│   ├── memory_manager.py         # Cache management
│   └── storage.py                # Storage backends
│
├── trust_safety/                 # Security & validation
│   ├── __init__.py
│   ├── safety_guard.py           # Input validation
│   ├── privacy_checker.py        # PII detection
│   └── rate_limiter.py           # Rate limiting
│
├── database/                     # Data persistence
│   ├── __init__.py
│   └── db_manager.py             # SQLite operations
│
├── data/
│   ├── ai_agent_system.db        # Auto-created on startup
│   └── uploads/                  # User uploaded files
│
├── logs/
│   └── ai_agent_system.log       # Application logs
│
├── assets/
│   ├── css/
│   │   └── style.css             # Frontend styling
│   ├── js/
│   │   └── app.js                # Frontend logic
│   └── img/                      # (Empty in Phase 0)
│
├── api_server.py                 # FastAPI main app
├── index.html                    # Frontend entry point
├── requirements.txt              # Python dependencies
├── .env.example                  # Configuration template
├── .gitignore                    # Git configuration
└── README.md                     # This file
```

---

## 🧪 Testing Phase 0

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

**Expected Response:**
```json
{
  "initialized": true,
  "components": {
    "database": "ok",
    "memory": "ok",
    "safety": "ok"
  },
  "agents": {
    "total_agents": 0,
    "agents_by_status": {},
    "agents_by_type": {}
  },
  "queue": {
    "total_queued": 0,
    "total_results_cached": 0,
    "status_breakdown": {}
  }
}
```

### Frontend Test

1. Open http://127.0.0.1:8000
2. Status badge should show "✅ System Ready"
3. Upload a test CSV file (Phase 1 agents needed for full functionality)

### Database Test

```python
from database import DatabaseManager

db = DatabaseManager()
db.initialize()

# Check database file created
# File should be at: data/ai_agent_system.db
```

---

## 📦 Configuration

### API Server (api_server.py)

```python
API_HOST = "127.0.0.1"         # Server address
API_PORT = 8000                # Server port
MAX_FILE_SIZE = 1 * 1024³      # 1GB max upload
```

### Database (database/db_manager.py)

```python
DATABASE_PATH = "data/ai_agent_system.db"
JOURNAL_MODE = "WAL"           # Write-Ahead Logging
TIMEOUT = 30                   # 30-second timeout
FOREIGN_KEYS = True            # Enforce referential integrity
```

### Memory (memory/memory_manager.py)

```python
DEFAULT_CACHE_SIZE = 1000      # Max cached items
DEFAULT_TTL = 3600            # 1-hour time-to-live
```

### Rate Limiting (trust_safety/rate_limiter.py)

```python
DEFAULT_MAX_REQUESTS = 100     # Requests per window
DEFAULT_WINDOW_SECONDS = 60    # 60-second window
```

### LLM Config (orchestrator/llm_config.py) - Phase 1

```python
LLM_ENABLED = False            # Disabled in Phase 0
LLM_MODEL = "mistral"          # Model selection
LLM_BASE_URL = "http://localhost:11434"  # Ollama default
LLM_MAX_TOKENS = 256           # CPU-optimized (i7-8750H)
```

---

## 🔌 API Endpoints

### System

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | System health check |
| GET | `/` | API info |

### Analysis

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/analyze` | Queue analysis task |
| GET | `/api/status/:task_id` | Get task status |
| GET | `/api/result/:task_id` | Get task result |
| POST | `/api/upload` | Upload file |

**Example: Queue Task**

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "file_123",
    "agent_id": "correlation_001",
    "payload": {"target": "signal_strength"}
  }'
```

**Response:**
```json
{
  "status": "queued",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Analysis task queued for processing"
}
```

---

## 📝 Development Guide

### Adding a New Agent (Phase 1)

1. **Create agent file** in `agents/` folder

```python
from orchestrator import BaseAgent

class CorrelationAgent(BaseAgent):
    def execute(self, task_input: dict) -> dict:
        # Implement your analysis logic
        result = self.process(task_input)
        return {
            "status": "completed",
            "output": result,
            "metadata": {}
        }
```

2. **Register agent** in `api_server.py`

```python
correlation_agent = CorrelationAgent(
    agent_id="correlation_001",
    name="Correlation Agent"
)
orchestrator.register_agent(correlation_agent)
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Task started")
logger.debug("Processing...")
logger.error("Error occurred")
```

Logs saved to: `logs/ai_agent_system.log`

### Database Operations

```python
from database import DatabaseManager

db = DatabaseManager()
db.initialize()

# Insert task
db.insert_task(
    task_id="task_123",
    agent_name="correlation_001",
    status="pending",
    payload={"data": "value"}
)

# Get task
task = db.get_task("task_123")

# Update status
db.update_task_status("task_123", "completed")
```

---

## 🛡️ Security & Safety

### Input Validation

All inputs validated by `SafetyGuard`:
- Payload size limits (1GB max)
- File format validation (.csv, .xlsx)
- File size validation
- PII detection (emails, phone, SSN, cards)

### Privacy

- **Zero cloud upload** - all data stays local
- **PII masking** available via `PrivacyChecker`
- **Rate limiting** prevents abuse

### Database

- **WAL mode** for data integrity
- **Foreign keys** enforce referential integrity
- **ACID transactions** for consistency

---

## 🚀 Phase 1 Preview

Phase 1 (5-6 weeks) will add:

1. **Correlation Analysis Agent**
   - Feature correlation computation
   - Statistical significance testing
   - Visualization support

2. **Forecasting Agent**
   - Time-series forecasting (ARIMA, Prophet)
   - Trend and seasonality detection
   - Confidence intervals

3. **Anomaly Detection Agent**
   - Isolation Forest algorithm
   - Local Outlier Factor (LOF)
   - Threshold-based alerting

4. **LLM Integration**
   - Ollama/LM Studio support
   - Local Mistral 7B inference
   - Analysis summarization

5. **Enhanced Frontend**
   - Results visualization
   - Interactive charts
   - Export functionality

---

## 📈 Performance Notes

### Hardware Specs

- **CPU:** Intel Core i7-8750H (6 cores, 2.2GHz)
- **RAM:** 32GB available
- **Storage:** SSD (~500MB/s)
- **GPU:** None (CPU-optimized)

### Performance Tuning

1. **FIFO Queue:** One task at a time (prevents CPU thrashing)
2. **Memory Limit:** ~10GB dataset max (leaves 22GB for system)
3. **Timeouts:** 120s per task (LLM inference: 30-60s)
4. **Caching:** LLM responses cached (5 max)

### Expected Timings (Phase 1)

- Correlation analysis: 10-30 seconds
- Forecasting: 20-40 seconds
- Anomaly detection: 15-25 seconds
- LLM inference: 30-60 seconds (CPU-only)

---

## 🐛 Troubleshooting

### API Won't Start

```
Error: Port 8000 already in use
```

Solution:
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or use different port
API_PORT=8001 python api_server.py
```

### Database Lock

```
Error: database is locked
```

Solution:
```bash
# Remove stale WAL files
rm data/ai_agent_system.db-wal
rm data/ai_agent_system.db-shm
```

### Import Errors

```
ModuleNotFoundError: No module named 'fastapi'
```

Solution:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### High Memory Usage

```
# Monitor memory
python -m memory_profiler api_server.py

# Clear memory cache
curl http://127.0.0.1:8000/api/memory/clear
```

---

## 📞 Support & Documentation

- **System Prompt:** See SYSTEM_PROMPT.md
- **Roadmap:** See COMPREHENSIVE_ROADMAP.md
- **Architecture:** See diagrams/ folder
- **Issues:** Check logs/ai_agent_system.log

---

## 📄 License

Internal use only. Telecom AI Multi-Agent System.

---

## ✅ Phase 0 Completion Checklist

- [x] API server starts without errors
- [x] Frontend loads at http://127.0.0.1:8000
- [x] Database auto-initializes
- [x] Health check endpoint works
- [x] All modules importable
- [x] Type hints 100% coverage
- [x] Error handling comprehensive
- [x] Logging functional
- [x] Code follows standards
- [x] Documented and tested

---

**Last Updated:** November 21, 2025  
**Next Phase:** Phase 1 (Correlation Analysis Agent) - 5-6 weeks
