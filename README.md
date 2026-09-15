# KALPA (कल्पा)
### AI-Powered Hyper-Local Livelihood & Business Advisory Platform for Rural Bharat
**Smart India Hackathon 2026 Prototype Repository**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Express](https://img.shields.io/badge/Express-4.19-000000?style=flat&logo=express&logoColor=white)](https://expressjs.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20PostGIS-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com)

---

## 1. Project Overview

**KALPA (कल्पा)** is an intelligent, hyper-local business advisory platform engineered specifically for grassroots entrepreneurs, Self-Help Groups (SHGs), and rural micro-enterprises across India. 

It transforms informal vernacular business ideas spoken or typed in regional languages into viable, credit-linked, and bankable enterprises. KALPA combines multilingual voice intake (powered by Sarvam AI), automated NIC-2008 classification, spatial radius analytics (OpenStreetMap + PostGIS), real-time commodity data (APMC Mandis), multi-agent LangGraph workflows, MSME/PMEGP financial feasibility modeling, and 360° risk evaluations.

---

## 2. Multi-Stage Advisory Pipeline

KALPA executes an end-to-end, multi-stage pipeline designed for grassroots advisory:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 KALPA MULTI-STAGE ENGINE                               │
└────────────────────────────────────────────────────────────────────────────────────────┘
  Stage 1: Multilingual Voice/Text Intake (Sarvam AI STT, Indic Numbers & Currencies)
     │
     ▼
  Stage 2: Business Classification & NIC 2008 5-Digit Code Mapping
     │
     ▼
  Stage 3: Structured Entrepreneur & Business Profile Canonicalization
     │
     ▼
  Stage 4: LangGraph Multi-Agent Orchestrator & Manager Agent
     │
     ▼
  Stage 4.5: Domain Knowledge & Benchmark Hub (Govt Schemes: PMEGP/Mudra, MSME Benchmarks)
     │
     ▼
  Stage 5 & 6: Live Market Intelligence Engine (OSM Overpass POIs + APMC Mandi Prices)
     │
     ▼
  Stage 8: Opportunity Evaluation Engine (Demand Gap, Saturation, Opportunity Score)
     │
     ▼
  Stage 9: Financial Analysis & Feasibility Engine (Capex/Opex, DSCR, Subsidy, Break-even)
     │
     ▼
  Stage 10: Entrepreneur Fit & Capability Evaluator (Skill, Experience, Risk Appetite)
     │
     ▼
  Stage 11: 360° Risk Analysis Engine (Supply Chain, Seasonal, Price, Mitigation Matrix)
     │
     ▼
  Stage 12 (Upcoming): Instant Bankable DPR (Detailed Project Report) & Credit Appraisal Export
```

### Key Stage Capabilities:
- **Stage 1 (Multilingual Intake)**: Supports Hindi, English, and Hinglish with Indic currency words (*"50 hazar"*, *"2.5 lakh"*, *"ek crore"*) and land units (*"bigha"*, *"acre"*). Integrates Sarvam AI `saaras:v4` Speech-to-Text with conversational clarification loops.
- **Stage 2 (Classification & NIC Mapping)**: Maps natural language queries to official 5-digit NIC-2008 codes, sub-classes, and 2-digit industry divisions with ambiguity detection.
- **Stage 3 (Structured Profile)**: Canonicalizes investment capacity, business intent, scale, and geo-coordinates into strongly typed Pydantic models.
- **Stage 4 (LangGraph Orchestrator)**: Coordinates multi-agent advisory workflows with stateful execution, node DAG tracking, and idempotent operations.
- **Stage 4.5 (Knowledge & Benchmark Hub)**: Houses government schemes (PMEGP, Mudra, StandUp India, PMFME, NRLM), district profiles, and KVIC cost benchmark datasets.
- **Stage 5 & 6 (Market Intelligence)**: Queries OpenStreetMap Overpass API for POIs within radius buffers (competitors, suppliers, transport hubs) + APMC Mandi commodity rates + Census demographics.
- **Stage 8 (Opportunity Evaluation)**: Evaluates local demand, supplier proximity, competitor saturation, and outputs a normalized Opportunity Index & Tier rating.
- **Stage 9 (Financial Engine)**: Computes Capex/Opex breakdowns, working capital cycles, break-even timelines, Debt Service Coverage Ratio (DSCR), scheme subsidies, and Bankability Feasibility Scores.
- **Stage 10 (Entrepreneur Profile Engine)**: Assesses entrepreneur domain fit, past experience, risk appetite, capital readiness, and operational strength.
- **Stage 11 (360° Risk Engine)**: Identifies operational, market, price volatility, regulatory, and supply chain risks with an actionable mitigation matrix.

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Frontend Client (React 18 + Vite)                    │
│                          http://localhost:5173                          │
│                                                                         │
│  • Journey Workflow Wizard         • Voice Input & Audio Waveforms      │
│  • Interactive Leaflet Maps        • Dynamic Radar & Gauge Charts       │
│  • Financial Feasibility Sliders   • Scheme Eligibility Cards           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP / JSON
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   Node.js API Gateway (Express.js)                      │
│                          http://localhost:3000                          │
│                                                                         │
│  • Request Validation & Routing    • Security (Helmet, CORS)            │
│  • Subsystem Health Monitoring     • Centralized Error Handling         │
│  • Reverse Proxy to AI Backend     • Static Asset & Logging Pipeline    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP Proxy (/api/*)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   Python AI Microservice (FastAPI)                      │
│                          http://localhost:8000                          │
│                                                                         │
│  ├── LangGraph Multi-Agent Orchestrator                                 │
│  ├── 11 Core Advisory Engines (Intake, NIC, Market, Finance, Risk...)   │
│  ├── Adapters: Groq (Llama-3.3-70b) / Sarvam AI (saaras:v4, 105b)       │
│  └── External Tool Layer: OpenStreetMap Overpass, APMC Mandi Data       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ SQLAlchemy 2.0 / PostGIS
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   PostgreSQL 16 + PostGIS + pgvector                    │
│                             localhost:5432                              │
│                                                                         │
│  • Spatial Geometries & Buffers    • NIC 2008 & Scheme Benchmarks       │
│  • Session & Analysis Store        • Vector Scaffolding (Future RAG)    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide React, React Router 6, Axios |
| **API Gateway** | Node.js, Express, Helmet, CORS, Morgan, Axios |
| **AI Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, LangChain, LangGraph |
| **LLMs & Speech** | Groq (`llama-3.3-70b-versatile`), Sarvam AI (`saaras:v4` STT, `sarvam-105b` LLM), OpenAI fallback |
| **Data & Spatial** | PostgreSQL 16, PostGIS 3.4, SQLAlchemy 2.0, Alembic, OpenStreetMap Overpass |
| **DevOps & Testing** | Docker, Docker Compose, Pytest, Pytest-Asyncio |

---

## 5. Repository Structure

```
KALPA SIH/
├── frontend/                     # React 18 + Vite Web Application
│   ├── src/
│   │   ├── components/           # Navigation, UI components, Layouts, Charts
│   │   ├── context/              # Global state management
│   │   ├── pages/                # Multi-stage pages (Intake, Classification,
│   │   │                         # MarketIntelligence, FinancialAnalysis,
│   │   │                         # EntrepreneurProfile, RiskEngine, DPR...)
│   │   ├── services/             # Axios API service integrations
│   │   ├── App.jsx               # Route definitions
│   │   └── main.jsx              # App entry point
│   ├── package.json
│   └── vite.config.js
│
├── gateway/                      # Node.js Express API Gateway
│   ├── src/
│   │   ├── controllers/          # Proxy & validation controllers for all stages
│   │   ├── middleware/           # Error handlers, logging, CORS
│   │   ├── routes/               # Express routing tables (/api/*)
│   │   └── server.js             # Gateway bootstrapper
│   └── package.json
│
├── ai-service/                   # FastAPI AI & Multi-Agent Backend
│   ├── app/
│   │   ├── agents/               # LangGraph state graph & adapters
│   │   ├── api/routes/           # FastAPI router endpoints (Stages 1 - 11)
│   │   ├── core/                 # Settings, Pydantic config, Logging
│   │   ├── database/             # PostGIS connection, models, migrations
│   │   ├── data/                 # NIC 2008 codes, schemes & benchmark JSONs
│   │   ├── engines/              # Core business engines (Intake, NIC, Profile)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # Market, Financial, Risk, Entrepreneur engines
│   │   └── tools/                # OpenStreetMap, APMC Mandi, Govt tools
│   ├── tests/                    # Comprehensive Pytest test suites (23+ files)
│   ├── requirements.txt
│   └── main.py
│
├── docker-compose.yml            # Multi-service container orchestration
├── .env.example                  # Environment configuration template
└── README.md                     # Project documentation
```

---

## 6. Environment Configuration (`.env`)

Copy the master `.env.example` to `.env` in the root directory:

```powershell
cp .env.example .env
```

### Complete Environment Variables Reference:

```env
# ==============================================================================
# 1. FRONTEND CONFIGURATION (React + Vite)
# ==============================================================================
VITE_API_GATEWAY_URL=http://localhost:3000/api

# ==============================================================================
# 2. NODE.JS API GATEWAY CONFIGURATION
# ==============================================================================
PORT=3000
NODE_ENV=development
AI_SERVICE_URL=http://localhost:8000
CORS_ORIGIN=http://localhost:5173

# ==============================================================================
# 3. FASTAPI AI SERVICE CONFIGURATION
# ==============================================================================
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO

# ==============================================================================
# 4. DATABASE & SPATIAL (PostgreSQL 16 + PostGIS)
# ==============================================================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=kalpa
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/kalpa
POSTGIS_ENABLED=true
PGVECTOR_ENABLED=false

# ==============================================================================
# 5. PRIMARY LLM PROVIDER (Groq / OpenAI)
# ==============================================================================
# Set provider: "groq" (recommended) or "openai"
LLM_PROVIDER=groq

# Groq API Configuration (Fast Llama-3.3 inference)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# OpenAI Configuration (Fallback/Alternative)
LLM_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o

# ==============================================================================
# 6. SARVAM AI (Indic Multilingual Voice STT & Indic LLM)
# ==============================================================================
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_STT_MODEL=saaras:v4
SARVAM_LLM_MODEL=sarvam-105b
SARVAM_LLM_ENABLED=true
SARVAM_LLM_ENDPOINT=https://api.sarvam.ai/v1/chat/completions

# ==============================================================================
# 7. OPTIONAL / FUTURE RAG EMBEDDINGS
# ==============================================================================
INDICTRANS_ENABLED=false
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

---

## 7. How to Run the Application

### Option A: Running with Docker Compose (Recommended)

This single command builds and starts PostgreSQL (with PostGIS), the FastAPI AI Backend, the Node.js API Gateway, and the React Frontend.

```powershell
# 1. Clone repository
git clone https://github.com/ShriyanshuKapsime/KALPA-SIH.git
cd "KALPA SIH"

# 2. Setup environment
cp .env.example .env

# 3. Start all containers
docker compose up --build
```

**Services will be accessible at:**
- **Frontend Dashboard**: `http://localhost:5173`
- **Node.js API Gateway**: `http://localhost:3000` (Health: `http://localhost:3000/health`)
- **FastAPI AI Docs & Swagger**: `http://localhost:8000/docs`
- **PostgreSQL / PostGIS**: `localhost:5432`

---

### Option B: Local Standalone Development (Manual Setup)

Run each service in a separate terminal:

#### Terminal 1: PostgreSQL + PostGIS
Make sure PostgreSQL with PostGIS extension is running on port 5432:
```powershell
# If using Docker just for Postgres:
docker run -d --name kalpa-postgres -p 5432:5432 -e POSTGRES_DB=kalpa -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres postgis/postgis:16-3.4
```

#### Terminal 2: FastAPI AI Backend Service
```powershell
cd ai-service

# Create and activate Python virtual environment
python -m venv venv
.\venv\Scripts\activate       # On Linux/macOS: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server with live hot-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Swagger UI / Interactive Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

#### Terminal 3: Node.js API Gateway
```powershell
cd gateway

# Install dependencies
npm install

# Start Express gateway with file watch
npm run dev
```
- Gateway Health: `http://localhost:3000/health`
- AI Microservice Proxy Health: `http://localhost:3000/health/ai`

#### Terminal 4: React Frontend Client
```powershell
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 8. API Endpoints Reference

All endpoints are accessible via the Gateway (`http://localhost:3000/api`) or directly on the AI service (`http://localhost:8000/api/v1`):

| Stage | Method | Gateway Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **System** | `GET` | `/api/health/ai` | Checks AI microservice & DB connectivity |
| **Stage 1: Intake** | `POST` | `/api/intake/text` | Processes vernacular text intake & extracts entities |
| | `POST` | `/api/intake/voice` | Sarvam AI STT audio transcription & intent parser |
| | `POST` | `/api/intake/continue` | Multi-turn intake clarification conversation |
| **Stage 2: Classification** | `POST` | `/api/classification/classify` | Maps input to 5-digit NIC 2008 & Industry Sector |
| | `GET` | `/api/classification/nic/:code` | Retrieves NIC code metadata & division hierarchy |
| **Stage 3: Profile** | `POST` | `/api/profile/build` | Creates normalized business & entrepreneur profile |
| | `GET` | `/api/profile/:id` | Fetches saved structured profile by analysis ID |
| **Stage 4: Orchestrator** | `POST` | `/api/orchestrator/start` | Initiates LangGraph multi-agent advisory workflow |
| | `GET` | `/api/orchestrator/workflow/:id`| Retrieves real-time workflow state & step statuses |
| **Stage 4.5: Knowledge Hub** | `GET` | `/api/knowledge/schemes` | Returns list of eligible govt schemes (PMEGP, Mudra) |
| | `POST` | `/api/knowledge/schemes/evaluate` | Evaluates entrepreneur scheme eligibility & subsidy |
| | `GET` | `/api/knowledge/benchmarks/financial` | Returns MSME & KVIC financial cost benchmarks |
| **Stage 5 & 6: Market Intel** | `POST` | `/api/market-intelligence/collect`| Gathers Overpass spatial POIs & Mandi market prices |
| | `POST` | `/api/market-intelligence/analyze`| Runs spatial proximity & market saturation models |
| | `GET` | `/api/market-intelligence/tools/health`| Live health check for Overpass & Mandi tools |
| **Stage 8: Opportunity** | `POST` | `/api/opportunity-evaluation/analyze`| Computes local demand score & opportunity index |
| **Stage 9: Financial** | `POST` | `/api/financial-analysis/analyze`| Computes Capex/Opex, DSCR, and bankability score |
| | `POST` | `/api/financial-analysis/calculator`| Interactive financial loan & subsidy calculator |
| **Stage 10: Entrepreneur** | `POST` | `/api/entrepreneur-profile/analyze`| Assesses skill fit, risk appetite, and readiness |
| **Stage 11: Risk Engine** | `POST` | `/api/risk-analysis/analyze`| 360° risk evaluation & actionable mitigations |

---

## 9. Running Automated Tests

The repository contains extensive automated test coverage across all pipeline stages:

```powershell
cd ai-service

# Run all test suites
pytest -v

# Run tests for specific pipeline stages:
pytest tests/test_intake_stage1.py -v
pytest tests/test_multilingual_intake_canonical.py -v
pytest tests/test_classification_stage2.py -v
pytest tests/test_profile_stage3.py -v
pytest tests/test_orchestrator_stage4.py -v
pytest tests/test_knowledge_hub_stage4_5.py -v
pytest tests/test_market_intelligence_stage5.py -v
pytest tests/test_market_intelligence_engine_stage6.py -v
pytest tests/test_opportunity_evaluation_engine_stage8.py -v
pytest tests/test_financial_engine_stage9.py -v
pytest tests/test_entrepreneur_profile_stage10.py -v
pytest tests/test_risk_engine_stage11.py -v
pytest tests/test_stage10_11_workflow_integration.py -v
```

---

## 10. Roadmap & Upcoming Milestones

- [x] **Stage 1**: Multilingual Voice/Text Intake with Sarvam AI STT & Indic parsing
- [x] **Stage 2**: Business Classification & NIC-2008 Mapping Engine
- [x] **Stage 3**: Structured Entrepreneur & Business Profile Canonicalization
- [x] **Stage 4**: LangGraph Multi-Agent Orchestrator & State Graph
- [x] **Stage 4.5**: Domain Knowledge Hub & Benchmark Datasets (Schemes, KVIC, Mandis)
- [x] **Stage 5 & 6**: Live Market Intelligence (OpenStreetMap Overpass + APMC Mandis)
- [x] **Stage 8**: Opportunity Evaluation Engine & Demand Gap Scoring
- [x] **Stage 9**: Financial Analysis, DSCR, Subsidy & Feasibility Engine
- [x] **Stage 10**: Entrepreneur Profile & Operational Capability Evaluator
- [x] **Stage 11**: 360° Risk Analysis Engine & Mitigation Matrix
- [ ] **Stage 12**: Automated Bankable DPR (Detailed Project Report) PDF & Credit Appraisal Generation
- [ ] **Stage 13**: Offline-first PWA sync for remote field workers

---

## 11. Team & License

Built with ❤️ for **Smart India Hackathon 2026**.

Distributed under the MIT License. See `LICENSE` for more information.
