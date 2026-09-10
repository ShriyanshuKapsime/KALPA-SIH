# KALPA (कल्पा)
### AI-Powered Hyper-Local Livelihood & Business Advisory Platform for Rural Bharat
**Smart India Hackathon 2026 Prototype Repository**

---

## 1. Project Overview
**KALPA** is an intelligent, hyper-local business advisory platform engineered specifically for grassroots entrepreneurs and SHGs across rural India. It transforms vernacular business ideas into viable, credit-linked, and bankable micro-enterprises through multilingual voice intake, spatial radius analytics, automated NIC classification, ML feasibility scoring, and instant DPR generation.

---

## 2. Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│              Frontend Client (React.js + Vite)              │
│                     http://localhost:5173                   │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Node.js API Gateway (Express)                   │
│                     http://localhost:3000                   │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / Internal Proxy
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             Python AI Backend (FastAPI)                     │
│                     http://localhost:8000                   │
│                                                             │
│  ├── LangGraph Agents (Manager, Market, Pivot Advisor)      │
│  ├── 9 Core Engines (Intake, NIC, Spatial, Feasibility...) │
│  ├── ML Pipelines (Demand & Feasibility Predictors)         │
│  └── Tool Layer (Govt Open Data, OpenStreetMap, APMC Mandi) │
└──────────────────────────────┬──────────────────────────────┘
                               │ SQLAlchemy / pgvector / PostGIS
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          PostgreSQL 16 + PostGIS + pgvector                 │
│                     localhost:5432                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide React, React Router
- **API Gateway**: Node.js, Express, Helmet, CORS, Morgan, Axios
- **AI & ML Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2, LangChain, LangGraph, Scikit-Learn, XGBoost, Pandas, NumPy
- **Database & Spatial RAG**: PostgreSQL 16, PostGIS, pgvector, SQLAlchemy 2.0, Alembic
- **Containerization**: Docker, Docker Compose

---

## 4. Repository Structure
```
KALPA SIH/
├── frontend/             # React + Vite client
│   ├── src/              # Components, Pages, Services, UI
│   ├── package.json
│   └── vite.config.js
│
├── gateway/              # Node.js Express API Gateway
│   ├── src/              # Config, Routes, Controllers, Middleware
│   ├── package.json
│   └── server.js
│
├── ai-service/           # FastAPI AI & Multi-Agent Backend
│   ├── app/
│   │   ├── api/          # Route handlers & dependencies
│   │   ├── core/         # Config & Logging
│   │   ├── database/     # SQLAlchemy models & session
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── agents/       # LangGraph agent interfaces
│   │   ├── engines/      # 9 Core Advisory engines
│   │   ├── ml/           # Demand & Feasibility ML pipelines
│   │   ├── knowledge/    # Domain & Benchmark RAG scaffolding
│   │   └── tools/        # External spatial & government tool clients
│   ├── alembic/          # DB migrations
│   ├── requirements.txt
│   └── main.py
│
├── docker-compose.yml    # Multi-container orchestration
├── .env.example          # Environment configuration template
└── .gitignore            # Git exclusion rules
```

---

## 5. Current Project Status

> [!IMPORTANT]
> **CURRENT STATUS: Project infrastructure initialized.**
> 
> **Phase 1 development has NOT started yet.**
> 
> Phase 1 will implement:
> 1. User Intake
> 2. Multilingual NLP Processing
> 3. Entity & Intent Extraction
> 4. Business Classification
> 5. NIC Mapping
> 6. Business Ontology Mapping
> 7. Structured Business & Entrepreneur Profile

---

## 6. How to Run the Services

### Option A: Local Development (3 Terminals)

#### 1. FastAPI AI Backend
```powershell
cd ai-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- Available at: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

#### 2. Node.js API Gateway
```powershell
cd gateway
npm install
npm run dev
```
- Available at: `http://localhost:3000`
- Health check: `http://localhost:3000/health`
- Downstream AI Health: `http://localhost:3000/health/ai`

#### 3. React Frontend
```powershell
cd frontend
npm install
npm run dev
```
- Available at: `http://localhost:5173`

---

### Option B: Run with Docker Compose
```powershell
docker compose up --build
```
This boots PostgreSQL + PostGIS, FastAPI AI Service, Node Gateway, and Frontend simultaneously.
