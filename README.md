# RationSaathi — Public Distribution, Without the Runaround

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-84%20Pytest%20%7C%2014%20Vitest%20Passed-success?style=flat)](https://github.com/rajjeet-saha/RationSaathi)
[![A11y](https://img.shields.io/badge/A11y-axe--core%20WCAG%202.1%20AA-blueviolet?style=flat)](https://www.deque.com/axe/)
[![License](https://img.shields.io/badge/License-MIT%20%2F%20Civic%20Prototype-lightgrey?style=flat)](https://github.com/rajjeet-saha/RationSaathi)

A privacy-preserving civic-service navigator prototype built for migrant households navigating India's Public Distribution System (PDS) and the **One Nation One Ration Card (ONORC)** initiative.

> ⚠️ **DEMO MODE — SYNTHETIC DATA ONLY**  
> **No government system or live database is connected.** No real entitlement amounts, biometric data, Aadhaar numbers, legal deadlines, shop stocks, receipts, or citizen identity records exist anywhere in this repository. All updates and filings use a clearly labelled **simulated adapter** (`SIM-*` receipts).

---

## 🌐 Project Links

| Resource | Link / Location | Description |
|---|---|---|
| **GitHub Repository** | [github.com/rajjeet-saha/RationSaathi](https://github.com/rajjeet-saha/RationSaathi) | Source code, tests, and documentation |
| **Frontend Web App** | `http://localhost:5173` | Interactive React + Vite civic dashboard |
| **Backend API Service** | `http://localhost:8000` | FastAPI service & deterministic rules engine |
| **Interactive API Docs** | `http://localhost:8000/api/docs` | Swagger UI OpenAPI documentation |
| **Alternative API Docs** | `http://localhost:8000/api/redoc` | ReDoc API specifications |
| **System Health Check** | `http://localhost:8000/api/v1/health` | Live JSON health & demo-mode status |

---

## 🎯 The Problem & The Mission

For migrant workers and rural households, navigating fair price shops and ration entitlements across state lines is fraught with friction, misinformation, and risk:
- **Fear of cancellation**: Attempting a routine update (like a misspelled name or age change) often leads to fear of accidentally deleting a family member or losing monthly grain allocations.
- **Stock uncertainty**: Families travel miles to Fair Price Shops (FPS) only to discover grain is out of stock, or that interstate portability rules for their state-pair are unverified.
- **Grievance black holes**: Complaints about withheld rations or faulty biometric ePOS machines languish without clear ownership or verified escalation timelines.

**RationSaathi** provides a transparent, protective civic interface that answers four questions clearly:
1. **What can I safely do today?**
2. **What is verified vs. unverified?**
3. **What still needs confirmation?**
4. **Who is responsible for the next step?**

---

## 🛡️ Core Safety & Privacy Properties (Enforced Server-Side)

1. **Blocked Before Submission**: A correction that could remove a member, disassociate an entitlement, or jeopardize legal quota status is **BLOCKED** with guidance, not simply warned about. Blocked proposals cannot be submitted (returns `HTTP 409 Conflict`).
2. **Strict Member Isolation**: Member sessions read only their own profile and allocations. Cross-household and cross-member reads are rejected. Facilitators require explicitly logged, revocable consent before opening any profile.
3. **In-Memory Ephemeral Tokens**: Session authentication credentials exist in-memory only on the client and are revoked immediately upon profile switch, tab exit, or timeout.
4. **Offline-First Truth in State**: Local drafts are clearly labelled `NOT SUBMITTED` and tracked with deterministic local references. A draft is never shown as submitted without a cryptographically verified adapter receipt.
5. **No False Escalations**: The status `OVERDUE` requires a *verified* official deadline; elapsed days alone never trigger premature accusations or false escalations.
6. **Differencing & $k$-Anonymity Suppression**: Public aggregate statistics enforce minimum group size ($k \ge 5$) and suppress complementary totals that could leak individual identities through subtraction.
7. **Monotone Provenance**: Household-reported data is tracked with provenance and is never conflated with or upgraded to official government records.

---

## 🏗️ Architecture & Technology Stack

```
                              ┌───────────────────────────────────┐
                              │     React 18 + Vite + TS UI       │
                              │  (A11y WCAG 2.1 AA, Lucide, CSS)  │
                              └─────────────────┬─────────────────┘
                                                │ REST / JSON (In-Memory Session)
                                                ▼
                              ┌───────────────────────────────────┐
                              │       FastAPI Backend Engine      │
                              │  (Python 3.11+, Pydantic v2)      │
                              └───────┬───────────────────┬───────┘
                                      │                   │
                  Deterministic Rules │                   │ SQLAlchemy 2.0 ORM
                                      ▼                   ▼
                      ┌──────────────────────┐    ┌──────────────────────┐
                      │ Portability & Safety │    │  SQLite (Local Demo) │
                      │ Rules (Versioned)    │    │  PostgreSQL (Prod)   │
                      └──────────────────────┘    └──────────────────────┘
```

| Layer | Technologies | Details |
|---|---|---|
| **Frontend** | React 18, TypeScript 5.7, Vite 6, Tailwind CSS 3.4, React Router 6, Lucide Icons | Accessible, high-contrast, multi-lingual civic UI |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, Uvicorn | Strict schema validation, session controls, safety engine |
| **Database** | SQLite (default demo) / PostgreSQL (production target) | Full Alembic migrations support |
| **Testing** | Pytest, HTTPX, Vitest, Testing Library, Axe-Core | Automated unit, regression, API, and accessibility test suites |
| **Safety Rules** | Pure deterministic JSON rule tables (`portability_rules.json`) | Verifiable, portable rules independent of external networks |

---

## 📁 Repository Structure

```
RationSaathi/
├── backend/                     # FastAPI backend application
│   ├── app/
│   │   ├── api/v1/              # API endpoints (sessions, households, drafts, grievances, public, etc.)
│   │   ├── adapters/            # Simulated submission adapters (SIM-* receipts)
│   │   ├── models/              # SQLAlchemy 2.0 database models
│   │   ├── rules/               # Portability rule engine & versioned JSON rules
│   │   ├── security/            # In-memory session deps, token revocation, rate limiting
│   │   └── services/            # Aggregates, grievances, evaluation services
│   ├── scripts/                 # Deterministic synthetic data generator (seed.py)
│   └── tests/                   # 84 comprehensive Pytest suites
├── frontend/                    # React 18 + Vite client application
│   ├── src/
│   │   ├── app/                 # App root, routing, session context
│   │   ├── components/          # Accessible UI library, Shell, Pictograms, ReadAloud, Status badges
│   │   ├── features/            # Feature pages (overview, migration, corrections, drafts, grievances)
│   │   ├── lib/                 # i18n localization dictionaries (English, Hindi, Bengali, Tamil, etc.)
│   │   └── test/                # Vitest & axe-core accessibility tests
├── database/                    # Alembic migration revisions
├── docs/                        # Architecture specs, threat models, evaluation reports
└── alembic.ini                  # Alembic database configuration
```

---

## ⚡ Quick Start Guide

### Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** & **npm** installed
- **Git**

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux:
# python3 -m venv .venv
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server (auto-creates database and seeds synthetic data on startup)
uvicorn app.main:app --reload --port 8000
```
Backend API will be running at **`http://localhost:8000`** (Swagger docs at `/api/docs`).

### 2. Frontend Setup

In a new terminal:
```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```
Open **`http://localhost:5173`** in your browser. Choose any synthetic profile (e.g., migrant household member or facilitator) to test the system.

---

## 🧪 Testing & Verification

RationSaathi includes thorough automated testing across both backend safety properties and frontend accessibility compliance:

### Backend Test Suite (Pytest)
```bash
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```
**84 passed tests** across:
- `test_smoke.py`: Health checks, demo mode isolation, synthetic seeding.
- `test_correction_api.py`: Destructive change blocking, redactions, idempotent submissions.
- `test_evaluation.py`: Harmful-correction recall (8/8 seeded attack cases caught and blocked).
- `test_drafts.py`: Offline queueing, state transitions, duplicate prevention.
- `test_grievance.py`: Deadline verification, escalation letter generation.
- `test_portability.py`: State-pair grain portability, stock freshness downgrade.
- `test_privacy_api.py`: Cross-member isolation, facilitator consent gates, token revocation.
- `test_aggregates.py`: $k$-anonymity and subtraction-differencing protection.

### Frontend Test Suite (Vitest & Axe-Core)
```bash
cd frontend
npm test
```
**14 passed tests** across:
- `status.test.tsx`: Verified vs. unverified status indicator badges.
- `corrections.test.tsx`: Visual blocked-risk warnings and submission disclaimers.
- `accessibility.test.tsx`: Automated **axe-core** scan verifying **0 WCAG violations**.

### Production Build & Type Checking
```bash
cd frontend
npm run build
```
Executes `tsc --noEmit` and bundles the production app into `dist/` with zero TypeScript errors.

---

## 🤝 Contributing

Contributions to civic technology, accessibility enhancements, and language localization are welcome!

1. Fork the Project ([github.com/rajjeet-saha/RationSaathi](https://github.com/rajjeet-saha/RationSaathi))
2. Create your Feature Branch (`git checkout -b feature/NewFeature`)
3. Commit your Changes (`git commit -m 'Add NewFeature'`)
4. Push to the Branch (`git push origin feature/NewFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

*Disclaimer: RationSaathi is an independent civic research and engineering prototype. It is not affiliated with or endorsed by any government department.*
