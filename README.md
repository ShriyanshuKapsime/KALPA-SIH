# KALPA (कल्पा)
### AI-Powered Hyper-Local Livelihood & Business Advisory Platform for Rural Bharat
**Smart India Hackathon 2026 Prototype Repository**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Express](https://img.shields.io/badge/Express-4.19-000000?style=flat&logo=express&logoColor=white)](https://expressjs.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20PostGIS-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Sarvam AI](https://img.shields.io/badge/Sarvam%20AI-Indic%20Voice%20%26%20LLM-FF6F00?style=flat)](https://www.sarvam.ai)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Project Overview & Vision

**KALPA (कल्पा)** is a full-lifecycle, hyper-local business advisory and post-launch enterprise management platform engineered specifically for grassroots entrepreneurs, Self-Help Groups (SHGs), Farmer Producer Organizations (FPOs), and rural micro-enterprises across Bharat.

In rural and semi-urban India, millions of aspiring entrepreneurs face insurmountable barriers: language barriers, lack of formalized business planning, inability to navigate complex government credit-linked schemes (PMEGP, Mudra, PMFME), lack of localized market spatial intelligence, and absence of continuous post-launch operational guidance.

**KALPA bridges this gap completely:**
1. **Intake to Viability**: Converts informal spoken or typed vernacular queries into structured business profiles mapped to official **5-digit NIC-2008** classifications.
2. **Spatial & Economic Intelligence**: Gathers live catchment intelligence using **OpenStreetMap Overpass API**, real-time commodity pricing from **APMC Mandis**, and Census demographic datasets.
3. **Deterministic Financial Modeling (M1–M6)**: Calculates project costs, means of finance, 5-year P&L cash flows, statutory income tax (AY 2026-27 under Sec 115BAC, 44AD, 44ADA, and corporate slabs), Debt Service Coverage Ratio (DSCR), Break-Even Point (BEP), and downside stress scenarios.
4. **Bank-Grade DPR Generation (Stage 14.1–14.3)**: Generates 10-section institutional credit appraisal PDFs matching Indian Public Sector Bank standards.
5. **Post-Launch Growth Manager & 24/7 AI Operating Advisor**: Empowers the entrepreneur post-launch with 12 operational modules (Cash Flow Forecaster, Smart Inventory, Mandi Supply Chain, Dynamic Pricing, Demand Radar, ONDC/Scheme Scaling, Digital Storefront, and Voice-first AI Advisor).

---

## 2. Complete End-to-End System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                FRONTEND CLIENT (React 18 + Vite)                                 │
│                                      http://localhost:5173                                       │
├────────────────────────────────────────────────┬─────────────────────────────────────────────────┤
│  • Multilingual Voice Input (Saaras:v4 STT)   │  • Interactive Leaflet Map & Spatial Radius     │
│  • Vernacular Audio Playback (Bulbul:v3 TTS)  │  • Real-time Financial Sliders & M1-M6 Models   │
│  • Multi-Stage Journey Wizard (Stages 1-14)    │  • 10-Section Bankable DPR Preview & PDF Engine │
│  • 4-Pillar Feasibility & Dynamic SWOT Matrix  │  • Growth Manager Post-Launch Operating System  │
└────────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                 │ HTTP / REST / WebSockets
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               NODE.JS API GATEWAY (Express.js)                                   │
│                                      http://localhost:3000                                       │
├────────────────────────────────────────────────┬─────────────────────────────────────────────────┤
│  • Reverse Proxy & Intelligent Request Routing │  • Subsystem Health & Readiness Telemetry       │
│  • Rate Limiting, Security Headers & CORS      │  • Unified Translation Layer & Entity Normalizer │
│  • Session State & Lineage Token Management    │  • Centralized Error & Exception Interceptors   │
└────────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                 │ HTTP Proxy (/api/v1/*)
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              AI MICROSERVICE ENGINE (FastAPI)                                    │
│                                      http://localhost:8000                                       │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │                             LangGraph Multi-Agent Orchestrator                               │ │
│ └──────────────────────────────────────────────────────────────────────────────────────────────┘ │
│  ├── Stage 1: Multilingual Intake & Indic Entity Extraction (Saaras:v4 + Indic Parsers)         │
│  ├── Stage 2: Business Classification & NIC-2008 Official 5-Digit Mapping Engine                │
│  ├── Stage 3: Canonical Entrepreneur & Business Profile Engine                                   │
│  ├── Stage 4.5: Domain Knowledge Hub (PMEGP, Mudra, PMFME, NRLM, KVIC Benchmark Repositories)   │
│  ├── Stage 5 & 6: Live Market Intelligence Engine (OSM Overpass POIs + APMC Mandi Commodity)    │
│  ├── Stage 8: Opportunity Evaluation Engine (Catchment Demand-Supply Gap & Saturation Index)   │
│  ├── Stage 9: Financial Planning Engine (Milestones M1–M6: Capex, 5-Yr P&L, AY 2026-27 Tax)    │
│  ├── Stage 10: Entrepreneur Profile & Capability Fit Evaluator                                   │
│  ├── Stage 11: Multi-Vector 360° Risk Engine & Actionable Mitigation Matrix                     │
│  ├── Stage 12: 4-Pillar Integrated Feasibility Engine & Decision Synthesis (Hard Gating)        │
│  ├── Stage 13: Dynamic Strategic SWOT Matrix & Action Roadmap (Sarvam AI LLM + Provenance)     │
│  ├── Stage 14 (14.1, 14.2, 14.3): Institutional Bankable DPR & Credit Appraisal PDF Generator   │
│  ├── Stage 15: 24/7 Personal AI Business Operating Assistant (Sarvam AI Grounded Voice/Chat)   │
│  └── Growth Manager: Post-Launch Operating System (12 Mission-Critical Micro-Enterprise Modules)│
└──────────────────────────┬───────────────────────────────────────────────────────┬───────────────┘
                           │ SQLAlchemy 2.0 / PostGIS                              │ External APIs
                           ▼                                                       ▼
┌──────────────────────────────────────────────────┐ ┌─────────────────────────────────────────────┐
│       POSTGRESQL 16 + POSTGIS + PGVECTOR         │ │     SARVAM AI & EXTERNAL SERVICES           │
│                  localhost:5432                  │ ├─────────────────────────────────────────────┤
│  • Spatial Geometries, Catchment Radius Buffers  │ │  • Sarvam Saaras:v4 Indic STT               │
│  • NIC-2008 Code & KVIC Benchmark Master Tables │ │  • Sarvam Bulbul:v3 Indic TTS               │
│  • Government Scheme Eligibility Matrices        │ │  • Sarvam-105b-conversations Indic LLM      │
│  • Session States, Lineage & Analysis Artifacts  │ │  • Groq LLaMA-3.3-70b-versatile Fallback    │
│  • Scoped Assistant Long-Term Memory             │ │  • OpenStreetMap Overpass Spatial API       │
│  • Growth Manager Operating Ledgers & Telemetry  │ │  • APMC Mandi Real-Time Commodity Price API │
└──────────────────────────────────────────────────┘ └─────────────────────────────────────────────┘
```

---

## 3. End-to-End 15-Stage Pipeline & Growth Manager Walkthrough

```
  [Stage 1: Vernacular Intake] ──► [Stage 2: NIC-2008 Code] ──► [Stage 3: Canonical Profile]
               │                                                          │
               ▼                                                          ▼
  [Stage 4.5: Knowledge Hub]   ◄── [Stage 4: LangGraph Orchestrator] ───► [Stage 5 & 6: OSM & Mandi]
               │                                                          │
               ▼                                                          ▼
  [Stage 9: Finance M1–M6]     ◄── [Stage 8: Opportunity Engine]     ───► [Stage 10: Entrepreneur Fit]
               │
               ├──────────────────────────┐
               ▼                          ▼
  [Stage 11: 360° Risk Engine] ──► [Stage 12: 4-Pillar Feasibility] ──► [Stage 13: Dynamic SWOT]
                                          │
                                          ▼
                               [Stage 14.1–14.3: Bankable DPR]
                                          │
                                          ▼
                     ╔═══════════════════════════════════════════╗
                     ║   GROWTH MANAGER & STAGE 15 AI ADVISOR   ║
                     ║    (Post-Launch Operating System)        ║
                     ╚═══════════════════════════════════════════╝
```

---

### Stage 1: Multilingual Voice/Text Intake & Indic Entity Extraction
- **Objective**: Remove literacy and language barriers by allowing entrepreneurs to speak or write naturally in Hindi, English, or Hinglish.
- **Voice Engine**: Integrates Sarvam AI `saaras:v4` Speech-to-Text with automatic language identification, background noise reduction, and custom lexicon biasing.
- **Indic Normalizer**: Parses spoken colloquial financial terms (*"50 hazar"*, *"2.5 lakh"*, *"ek peti"*, *"aadha crore"*) and agricultural units (*"bigha"*, *"kattha"*, *"acre"*, *"guntha"*).
- **Conversational Clarification**: If critical parameters (investment capacity, location, category) are ambiguous, triggers a dynamic multi-turn clarification loop.

---

### Stage 2: Business Classification & NIC-2008 5-Digit Code Mapping
- **Objective**: Standardize informal business descriptions into official National Industrial Classification (NIC-2008) 5-digit sub-classes.
- **Classification Engine**: Multi-tier semantic mapping combining exact keyword indexing, vector embeddings, and LLM-assisted disambiguation.
- **Hierarchical Enrichment**: Resolves 2-digit Major Division, 3-digit Group, 4-digit Class, and 5-digit Sub-class with industrial risk indicators, pollution classification (Red/Orange/Green/White), and regulatory licensing prerequisites.

---

### Stage 3: Structured Profile Canonicalization
- **Objective**: Structure unstructured entrepreneur responses into an immutable, strongly typed Pydantic profile.
- **Schema Fields**:
  - `personal_profile`: Name, age, gender, education, social category (General/OBC/SC/ST/Minority/Women/Ex-Servicemen), prior enterprise experience.
  - `business_intent`: Selected NIC code, proposed business name, target scale (Micro/Small).
  - `spatial_coordinates`: Latitude, longitude, rural/urban classification, district, state, pin code.
  - `financial_capacity`: Promoter own contribution capability, collateral availability, existing bank relationships.

---

### Stage 4: LangGraph Multi-Agent Orchestrator
- **Objective**: Manage asynchronous, resilient, multi-stage state transitions with lineage tracking.
- **Graph Topology**: Stateful DAG ensuring parallel data gathering (Market Intelligence, Knowledge Hub, Mandi Rates) followed by sequential deterministic evaluations (Opportunity -> Finance -> Risk -> Feasibility -> SWOT -> DPR -> Growth Manager).
- **Fault Tolerance**: Per-node retry policies, graceful degradation, and execution status callbacks.

```
       [Start]
          │
          ▼
   [Intake Canonicalized]
          │
     ┌────┴───────────────────────────┐
     ▼                                ▼
[Spatial Evidence Collector]     [Scheme & Benchmark Fetcher]
     │                                │
     └────┬───────────────────────────┘
          ▼
   [Opportunity Engine]
          │
          ▼
   [Financial Engine M1-M6]
          │
     ┌────┴───────────────────────────┐
     ▼                                ▼
[Entrepreneur Fit]              [Risk Engine]
     │                                │
     └────┬───────────────────────────┘
          ▼
   [4-Pillar Feasibility Synthesis]
          │
          ▼
   [Dynamic SWOT & Roadmap]
          │
          ▼
   [Stage 14.1-14.3 Bankable DPR]
          │
          ▼
   [Growth Manager Operating Loop]
```

---

### Stage 4.5: Domain Knowledge & Benchmark Hub
- **Objective**: Ingest and query authoritative government schemes and micro-enterprise financial cost benchmarks.
- **Scheme Rules Engine**:
  - **PMEGP (Prime Minister Employment Generation Programme)**: Computes 15% to 35% margin money subsidy based on location (Rural vs Urban) and beneficiary category (Special vs General).
  - **Pradhan Mantri Mudra Yojana (PMMY)**: Evaluates Shishu (up to ₹50k), Kishore (₹50k–₹5L), and Tarun (₹5L–₹10L) loan fitment.
  - **PMFME (PM Formalisation of Micro food processing Enterprises)**: 35% credit-linked capital subsidy up to ₹10 Lakhs.
  - **KVIC & MSME Benchmarks**: Sector-specific machinery cost tables, electricity unit requirements, raw material ratios, and labor norms across 100+ rural micro-industries.

---

### Stage 5 & 6: Live Market Intelligence Engine (OSM Overpass + APMC Mandis)
- **Objective**: Transform geographical coordinates into localized market intelligence.
- **Spatial Radius Buffers**:
  - Micro Catchment (1.5 km – 3.0 km): Local retail competitors, neighborhood population density, pedestrian footfall hubs.
  - Meso Catchment (5.0 km – 15.0 km): Wholesale markets, competing suppliers, transport junctions, cold storage facilities.
- **APMC Mandi Rates**: Queries real-time agricultural commodity prices, modal rates, and 30-day price trends across nearby regulated mandis.
- **Demographic Synthesis**: Computes purchasing power proxies, rural/urban ratio, and target household density.

---

### Stage 8: Opportunity Evaluation Engine
- **Objective**: Quantify market demand-supply gap and calculate a standardized Opportunity Index.
- **Formulas & Metrics**:
  - **Competitor Saturation Index ($S_c$)**:
    $$S_c = \frac{\text{Count of Direct Competitors in 3km Radius}}{\text{Benchmark Capacity Threshold}}$$
  - **Demand-Supply Gap Score ($G_d$)**:
    $$G_d = \min\left(100, \max\left(0, \frac{\text{Catchment Population} \times \text{Per Capita Consumption} - \text{Total Existing Supply}}{\text{Proposed Enterprise Capacity}} \times 100\right)\right)$$
  - **Composite Opportunity Score ($O_{\text{total}}$)**:
    $$O_{\text{total}} = 0.35 \times G_d + 0.25 \times (100 - S_c \times 100) + 0.20 \times P_{\text{purchasing\_power}} + 0.20 \times T_{\text{transport\_proximity}}$$
  - **Output Tiers**: `TIER_1_EXCELLENT` ($\ge 75$), `TIER_2_MODERATE` ($50 - 74$), `TIER_3_CHALLENGING` ($< 50$).

---

### Stage 9: Financial Planning Engine (Milestones M1 to M6)
- **Objective**: Execute deterministic, bank-compliant financial modeling and tax computation without LLM hallucinations.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        STAGE 9: FINANCIAL ENGINE PIPELINE (M1 - M6)                    │
└────────────────────────────────────────────────────────────────────────────────────────┘
  [M1: Archetype & Foundation]
   • Manufacturing / Retail / Service / Agro-Processing Resolution
   • Driver Evidence & Scale Bounds Validation
         │
         ▼
  [M2: Project Cost & Means of Finance]
   • Total Project Cost = Capex (Machinery + Civil + Pre-Op) + Working Capital
   • Promoter Margin (5% - 10%) + Bank Term Loan + Scheme Subsidy (PMEGP 15%-35%)
         │
         ▼
  [M3: 5-Year Financial Projections & Statutory Income Tax Resolver]
   • Revenue Escalation & Variable Cost Modeling
   • Straight-Line Method (SLM) Depreciation (Plant: 15%, Buildings: 10%, Furniture: 10%)
   • Statutory Indian Tax Resolver (AY 2026-27 / FY 2025-26 under Sec 115BAC / 44AD / 44ADA / Corporate)
         │
         ▼
  [M4: Banking Appraisal & Credit Health]
   • Debt Service Coverage Ratio (DSCR): DSCR_avg >= 1.75, DSCR_min >= 1.25
   • Break-Even Point (BEP % of Capacity): BEP = Fixed Costs / (Revenue - Variable Costs)
   • Interest Coverage Ratio (ICR) & Net Present Value (NPV)
         │
         ▼
  [M5: Financial Optimizer & Downside Stress Engine]
   • Sensitivity Analysis (Revenue -10%, Raw Material +10%, Interest +1.5%)
   • Scheme Optimization & Maximum Bank Loan Sanction Readiness
         │
         ▼
  [M6: Authoritative DPR Packager]
   • Produces canonical versioned `financial_context` (v1.0.0) consumed downstream
```

- **Statutory Indian Tax Resolver (AY 2026-27 / FY 2025-26)**:
  - **New Tax Regime (Section 115BAC)**:
    - Up to ₹4,00,000: Nil (0%)
    - ₹4,00,001 to ₹8,00,000: 5%
    - ₹8,00,001 to ₹12,00,000: 10%
    - ₹12,00,001 to ₹16,00,000: 15%
    - ₹16,00,001 to ₹20,00,000: 20%
    - ₹20,00,001 to ₹24,00,000: 25%
    - Above ₹24,00,000: 30%
    - Standard Rebate under Sec 87A: Full tax rebate if taxable income $\le ₹12,00,000$ (Effective zero tax up to ₹12 Lakhs).
    - Surcharge & 4% Health and Education Cess calculated strictly per IT Act.
  - **Presumptive Taxation Schemes**:
    - **Section 44AD (Small Business / Trading)**: Deemed profit at 8% of gross turnover (6% for digital/banking receipts).
    - **Section 44ADA (Professionals / Services)**: Deemed profit at 50% of gross receipts.
  - **Corporate Slabs**: Domestic MSME manufacturing companies (Section 115BAA/115BAB @ 15% / 22% + cess).

---

### Stage 10: Entrepreneur Profile & Capability Fit Evaluator
- **Objective**: Quantify the human element—evaluating whether the entrepreneur has the necessary skills, risk tolerance, and operational capacity to run the proposed business.
- **Evaluation Dimensions**:
  - **Technical & Domain Expertise (Weight: 30%)**: Prior experience in chosen sector, formal vocational training (PMKVY/RSETI).
  - **Financial & Capital Readiness (Weight: 25%)**: Own equity capability, credit history awareness, working capital reserve buffer.
  - **Managerial & Operational Capacity (Weight: 25%)**: Labor management, vendor negotiation, sales channel ownership.
  - **Risk Tolerance & Resilience (Weight: 20%)**: Downside risk readiness, adaptability to price fluctuations.

---

### Stage 11: Multi-Vector 360° Risk Engine
- **Objective**: Perform automated vulnerability testing across 7 risk vectors and generate a proactive risk mitigation matrix.
- **7 Risk Vectors**:
  1. **Supply Chain & Raw Material Risk**: Single-source dependency, seasonal raw material availability, mandi price volatility.
  2. **Market & Competition Risk**: Price wars from established players, low switching costs, localized market saturation.
  3. **Financial & Cash Flow Risk**: Extended debtor payment cycles, working capital dry-up, interest rate fluctuations.
  4. **Operational & Machinery Risk**: Power outages, equipment breakdown, lack of local spare parts or technicians.
  5. **Regulatory & Compliance Risk**: FSSAI food safety norms, GST filing non-compliance, local municipal trade licenses.
  6. **Environmental & Climate Risk**: Monsoon disruptions, heatwaves affecting perishable produce, flood/drought exposure.
  7. **Labor & Skill Risk**: Unavailability of skilled operators, high attrition during harvest seasons.
- **Output**: Each vector is assigned a Severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), Probability (`0.0` to `1.0`), Risk Impact Score, and a concrete, localized Mitigation Strategy.

---

### Stage 12: 4-Pillar Integrated Feasibility Engine & Decision Synthesis
- **Objective**: Synthesize Market, Financial, Entrepreneur, and Risk evaluations into a definitive enterprise viability decision with hard gating.
- **Four Weighted Pillars**:
  1. **Market Opportunity Score ($M$)** — 30% Weight
  2. **Financial Viability & DSCR Score ($F$)** — 35% Weight
  3. **Entrepreneur Capability Fit ($E$)** — 20% Weight
  4. **Risk Resilience Score ($R = 100 - \text{Risk Score}$)** — 15% Weight
- **Composite Viability Score**:
  $$\text{Feasibility Score} = 0.30 \times M + 0.35 \times F + 0.20 \times E + 0.15 \times R$$
- **Hard Critical Gates**:
  - Gate 1: If Average DSCR $< 1.15 \implies$ Automatic `NOT_FEASIBLE` (Credit non-serviceable).
  - Gate 2: If Promoter Equity Contribution is unverified and $< 5\% \implies$ `CONDITIONAL`.
  - Gate 3: If Raw Material Availability $< 40\% \implies$ `CONDITIONAL` with mandatory supplier tie-up.
- **Decision Outcomes**:
  - `VIABLE` ($\ge 70/100$ and passed all gates): Enterprise cleared for Bank DPR generation and loan submission.
  - `CONDITIONAL` ($50 - 69/100$): Cleared with required pre-launch conditions (e.g. higher equity, subsidy tie-up, vocational training).
  - `NOT_FEASIBLE` ($< 50/100$): Proposes intelligent pivot options (alternative NIC codes, smaller initial capex, service vs manufacturing).

---

### Stage 13: Dynamic Strategic SWOT Matrix & Action Roadmap
- **Objective**: Generate grounded, hyper-personalized SWOT matrices and sequential pre-launch roadmaps using Sarvam AI Indic LLMs (`sarvam-105b-conversations`).
- **Zero Hallucination Guarantee**: The LLM prompt is injected with deterministic context from Stages 1–12 (PMEGP subsidy figures, DSCR numbers, local competitor counts, Overpass POI names).
- **Provenance Citations**: Every SWOT item is tagged with its evidence source (e.g., `[Source: Stage 5 Overpass POI Analysis]`, `[Source: Stage 9 M4 Banking Model]`).
- **Interactive Execution**: Sub-10 second response time with automatic fallback to deterministic rule templates if external LLM latency limits are reached.

---

### Stage 14 (14.1, 14.2, 14.3): Bankable DPR & Credit Appraisal PDF Generator
- **Objective**: Produce institutional-grade Detailed Project Reports (DPRs) formatted according to Indian Public Sector Bank (SBI, PNB, BoB, Canara) credit appraisal guidelines.
- **Three-Tier Architecture**:
  - **Stage 14.1 (DPR Intake & Gap Discovery)**: Detects missing credit parameters (e.g. electricity load sanctioned, building ownership, supplier quotations).
  - **Stage 14.2 (Deterministic Inference & Benchmark Resolution)**: Resolves gaps using KVIC district cost benchmark databases and user overrides.
  - **Stage 14.3 (Institutional ReportLab PDF Engine)**: Compiles 10 formatted sections with tables, charts, and signatures.
- **10 Formal DPR Sections**:
  1. Executive Summary & Project At A Glance
  2. Promoter Background & KYC Details
  3. Business Concept, Products & Value Proposition
  4. Local Market Analysis & Catchment Demographics
  5. Technical Feasibility, Land, Civil Works & Plant Machinery Schedules
  6. Raw Material Sourcing, Utilities & Manpower Planning
  7. Means of Finance, Capex, Working Capital & PMEGP/Mudra Subsidy Integration
  8. 5-Year Financial Projections (Revenue, P&L, Balance Sheet, Cash Flow Schedules)
  9. Banking Ratios, Amortization Schedule, DSCR, BEP & Sensitivity Analysis
  10. Risk Mitigation Matrix, Implementation Schedule & Statutory Compliance Checklist

---

### Growth Manager: Post-Launch Operating System & 24/7 AI Business Advisor
- **Objective**: Micro-enterprises fail not just at launch, but during the first 12–24 months of operations due to cash flow missteps, stockouts, delayed collections, and unoptimized pricing. **Growth Manager** is KALPA's complete post-launch enterprise operating system.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             GROWTH MANAGER OPERATIONAL ARCHITECTURE                              │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  ┌───────────────────────┐   ┌──────────────────────────┐   ┌─────────────────────────────────┐  │
│  │ 1. Business Health    │   │ 2. AI Actionable Recs    │   │ 3. Cash Flow Forecaster         │  │
│  │    • Vitality: 92/100 │   │    • 1-Click Execution   │   │    • 30/90-Day Runway Alert     │  │
│  │    • EMI Coverage 10x │   │    • Priority Sorting    │   │    • Working Capital Monitor    │  │
│  └───────────────────────┘   └──────────────────────────┘   └─────────────────────────────────┘  │
│  ┌───────────────────────┐   ┌──────────────────────────┐   ┌─────────────────────────────────┐  │
│  │ 4. Smart Inventory    │   │ 5. Hyper-Local Supply    │   │ 6. Expense & Margin Optimizer   │  │
│  │    • SKU Stock Alerts │   │    • Mandi Rate Benchmrk │   │    • Fixed vs Variable Tracking │  │
│  │    • Spoilage Tracker │   │    • Lead Time Tracking  │   │    • Tax Receipt Vault          │  │
│  └───────────────────────┘   └──────────────────────────┘   └─────────────────────────────────┘  │
│  ┌───────────────────────┐   ┌──────────────────────────┐   ┌─────────────────────────────────┐  │
│  │ 7. Local Demand Radar │   │ 8. Dynamic Pricing       │   │ 9. Order & Delivery Queue       │  │
│  │    • +18% Surge Alert │   │    • Bulk Margin Matrix  │   │    • COD vs UPI Reconciliation  │  │
│  │    • Festive Forecast │   │    • Value-Bundle Engine │   │    • Dispatch Routing           │  │
│  └───────────────────────┘   └──────────────────────────┘   └─────────────────────────────────┘  │
│  ┌───────────────────────┐   ┌──────────────────────────┐   ┌─────────────────────────────────┐  │
│  │ 10. Enterprise Scale  │   │ 11. AI Voice Assistant   │   │ 12. Digital Storefront          │  │
│  │    • PMEGP 2nd Loan   │   │    • Sarvam 105b Model   │   │    • Instant Catalog Generator  │  │
│  │    • ONDC/GeM Portal  │   │    • Hindi/Voice STT/TTS │   │    • WhatsApp & QR Checkout    │  │
│  └───────────────────────┘   └──────────────────────────┘   └─────────────────────────────────┘  │
│                                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

#### The 12 Mission-Critical Operational Modules:

1. **Business Health & Vitality Scorecard**:
   - Computes real-time **Operational Health Index (0–100)** synthesizing cash buffer, EMI timeliness, inventory turns, and customer retention.
   - Highlights critical operating alerts (e.g., *"Upcoming Loan EMI of ₹18,450 in 8 days — Cash coverage is 10x safe"*).
2. **AI Actionable Recommendations Engine**:
   - Generates ranked, high-impact operational interventions across Cash Flow, Sourcing, Marketing, Pricing, and Statutory Compliance.
   - Allows one-click resolution and status tracking directly from the dashboard.
3. **Dynamic Cash Flow Forecaster & Runway Tracker**:
   - 30-day and 90-day predictive cash inflows vs outflows.
   - Automated Working Capital Deficit alarms when debtor receivables lag beyond 21 days.
4. **Smart Inventory & Stockout Alert Engine**:
   - SKU-level minimum safety stock thresholds and reorder quantity suggestions.
   - Specialized perishable produce spoilage tracking for agro-processing and dairy units.
5. **Hyper-Local Supply Chain & Mandi Comparison**:
   - Tracks active supplier orders, transit lead times, and vendor delivery reliability.
   - Cross-references raw material purchase prices with real-time APMC Mandi benchmark rates to ensure margin protection.
6. **Expense Categorization & Margin Optimizer**:
   - Real-time classification into Raw Materials, Labor, Power/Utilities, Logistics, and Marketing.
   - Highlights cost leaks and suggests bulk procurement or alternative local vendors.
7. **Hyper-Local Demand Radar & Surge Detection**:
   - Identifies localized demand shifts (+18% morning delivery inquiries within 1.5 km radius).
   - Seasonality and regional festival calendar demand boosters.
8. **Smart Pricing & Value-Bundle Engine**:
   - Dynamic gross margin calculators for single and wholesale volumes.
   - Recommends bundle deals to increase Average Order Value (AOV).
9. **Order Management & Fulfillment Queue**:
   - Tracks incoming orders from Pending, Processing, Out-for-Delivery, to Completed.
   - Reconciles Cash-on-Delivery (COD) collections against digital UPI QR receipts.
10. **Enterprise Growth & Scheme Scaling Pathways**:
    - **PMEGP Second Loan Scheme**: Roadmap for expanding units with up to ₹1.00 Crore upgrade loans and 15% subsidy.
    - **ONDC & GeM Portal Onboarding**: Step-by-step digital integration guide to sell directly to institutional buyers and government departments.
    - **Mudra Kishore to Tarun Upgrade**: Automated eligibility evaluation for scaling working capital limits.
11. **24/7 AI Business Operating Assistant**:
    - Grounded conversational advisory powered by Sarvam AI (`sarvam-105b-conversations`).
    - Speech-to-Text (`saaras:v4`) and Text-to-Speech (`bulbul:v3`) in regional languages.
    - Deeply integrated with the entrepreneur's live ledger, DPR baseline figures, and inventory records.
12. **Digital Vernacular Storefront & Direct Commerce**:
    - Instant digital catalog generator with photo capture, pricing, and stock sync.
    - Instant shareable WhatsApp store links and dynamic UPI QR code generator for zero-commission vernacular selling.

---

## 4. Technology Stack

| Layer | Technologies & Libraries |
| :--- | :--- |
| **Frontend UI** | React 18, Vite 5, Tailwind CSS, Lucide React, Leaflet Maps, React Router 6, Axios |
| **API Gateway** | Node.js 20, Express.js 4.19, Helmet, CORS, Morgan, Axios, Multer |
| **AI Backend Service** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, LangChain, LangGraph, ReportLab PDF Engine |
| **Indic Voice & AI Models** | **Sarvam AI**: `saaras:v4` (Speech-to-Text), `bulbul:v3` (Text-to-Speech), `sarvam-105b-conversations` (Indic LLM) |
| **Fallback LLMs** | Groq (`llama-3.3-70b-versatile`), OpenAI (`gpt-4o`) |
| **Spatial & Databases** | PostgreSQL 16, PostGIS 3.4, SQLAlchemy 2.0, Alembic, OpenStreetMap Overpass API |
| **Live External Data** | OpenStreetMap Overpass Spatial Engine, Data.gov.in APMC Mandi Price Feeds |
| **DevOps & Containers** | Docker, Docker Compose, Pytest, Pytest-Asyncio |

---

## 5. Repository Directory Structure

```
KALPA SIH/
├── frontend/                         # React 18 + Vite Frontend Application
│   ├── src/
│   │   ├── components/               # Reusable UI & Stage Components:
│   │   │   ├── common/               # StartupLoader, Navigation, Header, LanguageSelector
│   │   │   ├── growth/               # GrowthManagerLaunchCard, TransitionOverlays
│   │   │   ├── journey/              # KalpaJourneyCarousel, Stage Steppers
│   │   │   ├── maps/                 # Leaflet Overpass Catchment Map Visualizers
│   │   │   └── ui/                   # Modal, Badges, Sliders, Cards
│   │   ├── context/                  # Global Context (WorkflowContext, LanguageContext)
│   │   ├── pages/                    # 16 Complete Stage Pages:
│   │   │   ├── Home/                 # Landing Page & Video Hero Banner
│   │   │   ├── Intake/               # Stage 1 Vernacular Voice/Text Intake
│   │   │   ├── Classification/       # Stage 2 NIC-2008 Classification
│   │   │   ├── Profile/              # Stage 3 Structured Entrepreneur Profile
│   │   │   ├── Orchestrator/         # Stage 4 Multi-Agent DAG State Monitor
│   │   │   ├── Knowledge/            # Stage 4.5 Government Scheme Knowledge Hub
│   │   │   ├── MarketIntelligence/   # Stage 5 & 6 Overpass POI & Mandi Radar
│   │   │   ├── OpportunityEvaluation/# Stage 8 Demand-Supply Gap & Saturation
│   │   │   ├── FinancialAnalysis/    # Stage 9 M1-M6 Financial Projections & Tax
│   │   │   ├── EntrepreneurProfile/  # Stage 10 Capability Fitment
│   │   │   ├── RiskEngine/           # Stage 11 360° Risk Analysis & Mitigations
│   │   │   ├── Feasibility/          # Stage 12 4-Pillar Decision Synthesis
│   │   │   ├── SWOT/                 # Stage 13 Dynamic SWOT & Action Roadmap
│   │   │   ├── DPR/                  # Stage 14.1-14.3 Bankable DPR Generator & PDF Preview
│   │   │   ├── Assistant/            # Stage 15 24/7 AI Business Assistant Page
│   │   │   └── GrowthManager/        # Growth Manager Post-Launch Operating OS
│   │   ├── services/                 # Axios API Service Modules (`api.js`)
│   │   ├── App.jsx                   # React Router Configuration & Stage Paths
│   │   └── main.jsx                  # React DOM Entrypoint
│   ├── package.json
│   └── vite.config.js
│
├── gateway/                          # Express.js API Gateway (Port 3000)
│   ├── src/
│   │   ├── controllers/              # Stage Controllers (Intake, NIC, DPR, Growth...)
│   │   ├── middleware/               # CORS, Request Logging, Error Interceptors
│   │   ├── routes/                   # Routing Table (`apiRoutes.js`, `healthRoutes.js`)
│   │   └── server.js                 # Gateway Bootstrapper
│   └── package.json
│
├── ai-service/                       # FastAPI AI & Deterministic Backend (Port 8000)
│   ├── app/
│   │   ├── agents/                   # LangGraph Multi-Agent Orchestrator DAG
│   │   ├── api/routes/               # FastAPI API Endpoints (/api/v1/*)
│   │   ├── core/                     # Configuration, Settings, Logging, Security
│   │   ├── data/                     # NIC-2008 master catalogs, KVIC benchmark JSONs
│   │   ├── database/                 # SQLAlchemy 2.0 Engine & PostGIS Models
│   │   ├── dpr/                      # Stage 14.1, 14.2 & 14.3 Institutional PDF Engine
│   │   ├── engines/                  # Core Business Engines (Intake, NIC, Market, DPR)
│   │   ├── knowledge/                # Benchmark Repositories & Scheme Rules
│   │   ├── schemas/                  # Pydantic v2 Request/Response Schemas
│   │   ├── services/                 # Core Deterministic Services:
│   │   │   ├── financial_engine/     # M1-M6 Financial Engine & AY 2026-27 Tax Policy
│   │   │   ├── swot_engine/          # Dynamic SWOT Agent & Deterministic Fallback
│   │   │   ├── assistant_engine/     # Grounded Conversational Memory & Chat Service
│   │   │   └── sarvam_llm_service.py # Sarvam AI API Integration Client
│   │   └── tools/                    # OSM Overpass, Mandi Rates, Census Tools
│   ├── tests/                        # 30+ Pytest Test Suites (M1-M6, DPR, SWOT, etc.)
│   ├── requirements.txt
│   └── main.py
│
├── docker-compose.yml                # Unified Multi-Service Docker Orchestration
├── .env.example                      # Master Environment Configuration Template
└── README.md                         # Complete System Documentation
```

---

## 6. Environment Configuration (`.env`)

To configure the platform, copy `.env.example` to `.env` in the repository root:

```powershell
cp .env.example .env
```

### Complete `.env` Reference:

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
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

LLM_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o

# ==============================================================================
# 6. SARVAM AI (Indic Voice STT/TTS & Indic LLM)
# ==============================================================================
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_STT_MODEL=saaras:v4
SARVAM_TTS_MODEL=bulbul:v3
SARVAM_TTS_SPEAKER=shreya
SARVAM_LLM_MODEL=sarvam-105b-conversations
SARVAM_ASSISTANT_MODEL=sarvam-105b-conversations
SARVAM_ASSISTANT_TIMEOUT=90.0
SARVAM_LLM_ENABLED=true
SARVAM_LLM_ENDPOINT=https://api.sarvam.ai/v1/chat/completions
```

---

## 7. How to Run the Application

### Option A: Running with Docker Compose (Recommended)

Start the entire KALPA ecosystem (Database, AI Service, API Gateway, and Frontend) with a single command:

```powershell
# 1. Clone repository
git clone https://github.com/ShriyanshuKapsime/KALPA-SIH.git
cd "KALPA SIH"

# 2. Prepare environment file
cp .env.example .env

# 3. Start all microservices in containers
docker compose up --build
```

**Live Service Endpoints:**
- **Frontend Web Application**: `http://localhost:5173`
- **Node.js API Gateway**: `http://localhost:3000` (Health: `http://localhost:3000/health`)
- **FastAPI AI Docs & Swagger**: `http://localhost:8000/docs`
- **PostgreSQL / PostGIS**: `localhost:5432`

---

### Option B: Local Standalone Development (Manual Setup)

Run each service in a separate terminal:

#### Terminal 1: PostgreSQL + PostGIS Database
```powershell
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

# Start FastAPI server with live reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger Documentation: `http://localhost:8000/docs`
- Service Health: `http://localhost:8000/health`

#### Terminal 3: Node.js API Gateway
```powershell
cd gateway

# Install dependencies
npm install

# Start Express gateway with nodemon watch
npm run dev
```
- Gateway Health: `http://localhost:3000/health`
- Microservice Proxy Health: `http://localhost:3000/health/ai`

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

## 8. Complete API Endpoints Reference

All endpoints are accessible via the Gateway (`http://localhost:3000/api`) or directly on the AI service (`http://localhost:8000/api/v1`):

| Category / Stage | Method | Gateway Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **System Health** | `GET` | `/api/health/ai` | Live check for AI microservice & DB connectivity |
| **Translation Engine** | `POST` | `/api/translate/text` | Translates vernacular text with Indic context |
| | `POST` | `/api/translate/batch` | Batch translation for UI keys & dictionaries |
| | `POST` | `/api/translate/object` | Deep JSON object translation preserving schema |
| **Stage 1: Intake** | `POST` | `/api/intake/text` | Processes vernacular text intake & extracts entities |
| | `POST` | `/api/intake/voice` | Sarvam AI Saaras:v4 audio transcription & intent |
| | `POST` | `/api/intake/transcribe` | Audio file to Indic text transcription |
| | `POST` | `/api/intake/continue` | Multi-turn conversational clarification loop |
| | `GET` | `/api/intake/session/:id` | Fetches saved intake session state |
| **Stage 2: Classification** | `POST` | `/api/classification/classify` | Maps business query to official 5-digit NIC-2008 code |
| | `POST` | `/api/classification/clarify` | Disambiguates borderline NIC industrial classes |
| | `GET` | `/api/classification/nic/:code` | Returns NIC code division, group & license requirements |
| | `GET` | `/api/classification/:id` | Retrieves saved classification session by ID |
| **Stage 3: Profile** | `POST` | `/api/profile/build` | Builds canonical entrepreneur & business profile |
| | `GET` | `/api/profile/session/:id` | Fetches profile by session ID |
| | `GET` | `/api/profile/:id` | Fetches profile by analysis ID |
| **Stage 4: Orchestrator** | `POST` | `/api/orchestrator/start` | Spawns LangGraph multi-agent advisory DAG execution |
| | `GET` | `/api/orchestrator/status/:id`| Returns node-by-node execution state & progress |
| | `GET` | `/api/orchestrator/workflow/:id`| Detailed step DAG status & artifact outputs |
| **Stage 4.5: Knowledge Hub** | `GET` | `/api/knowledge/schemes` | Returns list of eligible govt schemes (PMEGP, Mudra) |
| | `POST` | `/api/knowledge/schemes/evaluate` | Evaluates entrepreneur scheme eligibility & subsidy |
| | `GET` | `/api/knowledge/benchmarks/financial` | Returns sector financial capex/opex benchmarks |
| | `GET` | `/api/knowledge/benchmarks/market` | Returns market demand & turnover benchmarks |
| | `GET` | `/api/knowledge/business-profiles` | Pre-configured rural micro-enterprise models |
| **Stage 5 & 6: Market Intel** | `POST` | `/api/market-intelligence/collect`| Fetches Overpass POIs within radius buffers & Mandi rates |
| | `POST` | `/api/market-intelligence/analyze`| Computes spatial density, saturation & supplier proximity |
| | `GET` | `/api/market-intelligence/tools/health`| Health status of Overpass API & Mandi price feeds |
| **Stage 8: Opportunity** | `POST` | `/api/opportunity-evaluation/analyze`| Computes Demand-Supply Gap Score & Opportunity Tier |
| | `GET` | `/api/opportunity-evaluation/health` | Opportunity Engine self-test & status |
| **Stage 9: Financial** | `POST` | `/api/financial-analysis/analyze`| Computes M1-M6 Capex/Opex, 5-Yr P&L, AY 2026-27 Tax, DSCR |
| | `POST` | `/api/financial-analysis/calculator`| Real-time financial loan & subsidy parameter calculator |
| | `POST` | `/api/financial-analysis/dpr-package`| Generates canonical DPR financial context payload |
| **Stage 10: Entrepreneur** | `POST` | `/api/entrepreneur-profile/analyze`| Evaluates domain experience, risk readiness & skill fit |
| | `POST` | `/api/entrepreneur-profile/clarify`| Resolves skill gap questions & training options |
| **Stage 11: Risk Engine** | `POST` | `/api/risk-analysis/analyze`| 360° evaluation across 7 vectors & mitigation matrix |
| **Stage 12: Feasibility** | `POST` | `/api/feasibility/analyze` | 4-Pillar feasibility synthesis & hard decision gating |
| | `POST` | `/api/feasibility/pivot-suggestions`| Proposes intelligent pivot options for conditional cases |
| **Stage 13: Dynamic SWOT** | `POST` | `/api/swot/analyze` | Generates verified SWOT matrix with provenance citations |
| | `POST` | `/api/swot/stream` | Streams live SWOT roadmap tokens via SSE |
| **Stage 14.1: DPR Intake** | `GET` | `/api/dpr/gap-analysis/:id` | Discovers missing parameters for bank credit appraisal |
| | `POST` | `/api/dpr/question/answer/:id`| Ingests user answer for gap parameter resolution |
| | `POST` | `/api/dpr/benchmark/accept/:id`| Accepts default KVIC benchmark value for a parameter |
| **Stage 14.2: Enrichment** | `POST` | `/api/dpr/14.2/enrichment/run/:id`| Executes deterministic inference on resolved parameters |
| | `GET` | `/api/dpr/14.2/validation/:id`| Validates bank appraisal compliance and completeness |
| **Stage 14.3: Bankable DPR** | `POST` | `/api/dpr/14.3/generate/:id`| Compiles 10-section institutional DPR ReportLab PDF |
| | `GET` | `/api/dpr/14.3/download/:id`| Downloads generated bank-grade DPR PDF document |
| | `GET` | `/api/dpr/14.3/preview/:id` | Streams PDF preview buffer for in-browser viewer |
| **Stage 15: AI Assistant** | `POST` | `/api/assistant/chat` | Conversational query grounded in Stages 3–14 data |
| | `POST` | `/api/assistant/stt` | Sarvam Saaras:v4 voice audio speech-to-text |
| | `POST` | `/api/assistant/tts` | Sarvam Bulbul:v3 audio voice speech synthesis |
| | `GET` | `/api/assistant/history/:id` | Retrieves scoped multi-turn conversation history |
| | `DELETE` | `/api/assistant/history/:id` | Clears conversation memory for a session |
| **Growth Manager OS** | `GET` | `/growth-manager` (UI View) | Comprehensive 12-Module Post-Launch Operating System |

---

## 9. Automated Testing & Verification Suite

The backend contains extensive automated test suites covering every deterministic model, financial formula, tax slab, and multi-agent stage:

```powershell
cd ai-service

# Run all automated test suites:
python -m pytest

# Run specific stage test suites:
python -m pytest tests/test_intake_stage1.py -v
python -m pytest tests/test_multilingual_intake_canonical.py -v
python -m pytest tests/test_classification_stage2.py -v
python -m pytest tests/test_profile_stage3.py -v
python -m pytest tests/test_orchestrator_stage4.py -v
python -m pytest tests/test_knowledge_hub_stage4_5.py -v
python -m pytest tests/test_market_intelligence_stage5.py -v
python -m pytest tests/test_market_intelligence_engine_stage6.py -v
python -m pytest tests/test_opportunity_evaluation_engine_stage8.py -v
python -m pytest tests/test_financial_foundation_milestone1.py -v
python -m pytest tests/test_project_cost_milestone2.py -v
python -m pytest tests/test_financial_projection_milestone3.py -v
python -m pytest tests/test_banking_appraisal_milestone4.py -v
python -m pytest tests/test_financial_optimizer_milestone5.py -v
python -m pytest tests/test_dpr_packager_milestone6.py -v
python -m pytest tests/test_finance_to_downstream_integration.py -v
python -m pytest tests/test_entrepreneur_profile_stage10.py -v
python -m pytest tests/test_risk_engine_stage11.py -v
python -m pytest tests/test_stage13_swot_agent.py -v
python -m pytest tests/test_assistant_stage15.py -v
```

---

## 10. Implementation Status & Roadmap

- [x] **Stage 1**: Multilingual Voice/Text Intake with Sarvam AI STT & Indic parsing
- [x] **Stage 2**: Business Classification & NIC-2008 Official 5-Digit Mapping Engine
- [x] **Stage 3**: Structured Entrepreneur & Business Profile Canonicalization
- [x] **Stage 4**: LangGraph Multi-Agent Orchestrator & State DAG Engine
- [x] **Stage 4.5**: Domain Knowledge Hub & Benchmark Datasets (PMEGP, Mudra, PMFME, KVIC)
- [x] **Stage 5 & 6**: Live Market Intelligence (OpenStreetMap Overpass + APMC Mandi Rates)
- [x] **Stage 8**: Opportunity Evaluation Engine & Demand-Supply Gap Scoring
- [x] **Stage 9**: Financial Planning Engine (M1–M6: Capex/Opex, 5-Yr Projections, AY 2026-27 Tax, DSCR, Stress Testing)
- [x] **Stage 10**: Entrepreneur Profile & Operational Capability Fit Evaluator
- [x] **Stage 11**: Multi-Vector 360° Risk Analysis Engine & Actionable Mitigation Matrix
- [x] **Stage 12**: 4-Pillar Integrated Feasibility Synthesis & Decision Gating Engine
- [x] **Stage 13**: Dynamic Strategic SWOT Matrix & Action Roadmap Agent (Sarvam AI LLM)
- [x] **Stage 14 (14.1–14.3)**: Bankable DPR (Detailed Project Report) & Institutional PDF Generator
- [x] **Stage 15**: 24/7 Personal AI Business Assistant (Voice STT/TTS + Grounded Advisory)
- [x] **Growth Manager**: Post-Launch Micro-Enterprise Operating System (12 Operating Modules)
- [ ] **Stage 16**: Offline-first PWA synchronization for remote field workers and rural SHG animators

---

## 11. Team & License

Built with ❤️ for **Smart India Hackathon 2026**.

Distributed under the **MIT License**. See `LICENSE` for more information.
