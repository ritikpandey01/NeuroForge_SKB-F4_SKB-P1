# CarbonLens — Architecture

Digital Intelligent Platform for ESG Performance & GHG Monitoring.

---

## 1. System Overview

CarbonLens is a full-stack web application with a Python FastAPI backend, a React (Vite) frontend, and SQLite for persistence (swappable to PostgreSQL). Claude API powers the AI features: document parsing, anomaly explanation, scenario narratives, and report drafting. ReportLab/WeasyPrint renders assurance-ready PDF reports.

```
┌──────────────────────────────────────────────────────────────┐
│  Browser (React + Vite + Tailwind + shadcn/ui + Recharts)    │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS (JSON)
┌───────────────────────────▼──────────────────────────────────┐
│  FastAPI (Python)                                            │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Routers   │→ │  Services    │→ │  DB (SQLAlchemy ORM) │  │
│  │  (api/v1)  │  │  (business)  │  │                      │  │
│  └────────────┘  └──────┬───────┘  └──────────┬───────────┘  │
│                         │                     │              │
│                   ┌─────▼──────┐       ┌──────▼─────────┐    │
│                   │ Claude API │       │ SQLite /       │    │
│                   │  Client    │       │ PostgreSQL     │    │
│                   └────────────┘       └────────────────┘    │
│                         │                                    │
│                   ┌─────▼──────┐                             │
│                   │ ReportLab  │  ← PDF reports              │
│                   └────────────┘                             │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Folder Structure

```
ESG-Platform/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app factory, CORS, router mount
│   │   ├── core/
│   │   │   ├── config.py              # env-driven settings (pydantic-settings)
│   │   │   ├── claude_client.py       # single Claude wrapper + circuit breaker
│   │   │   └── logging.py
│   │   ├── db/
│   │   │   ├── base.py                # SQLAlchemy declarative base
│   │   │   ├── session.py             # engine, SessionLocal, get_db dep
│   │   │   ├── models/                # one file per table (organization.py, facility.py, ...)
│   │   │   └── migrations/            # Alembic
│   │   ├── schemas/                   # Pydantic request/response DTOs
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── activity.py        # /api/activity-data
│   │   │       ├── emissions.py       # /api/emissions, /api/calculate
│   │   │       ├── factors.py         # /api/emission-factors
│   │   │       ├── suppliers.py       # /api/suppliers
│   │   │       ├── scenarios.py       # /api/scenarios
│   │   │       ├── anomalies.py       # /api/anomalies
│   │   │       ├── reports.py         # /api/reports
│   │   │       ├── dashboards.py      # /api/dashboard/*
│   │   │       ├── uploads.py         # /api/upload/csv, /api/upload/document
│   │   │       └── audit.py           # /api/audit-log
│   │   ├── services/
│   │   │   ├── calculation_engine.py  # Module 2: factor match → co2e
│   │   │   ├── anomaly_detector.py    # Module 4A: stats + Claude explanation
│   │   │   ├── scenario_engine.py     # Module 4B: pure (baseline, levers) → trajectory
│   │   │   ├── document_parser.py     # Module 1: PDF/image → Claude → JSON
│   │   │   ├── report_builder.py      # Module 5: BRSR/GRI/TCFD assemblers
│   │   │   ├── supplier_scoring.py    # maturity + data quality
│   │   │   ├── validator.py           # >2σ rule, range checks, unit checks
│   │   │   └── audit.py               # write audit_log row for every mutation
│   │   ├── seed/
│   │   │   ├── factors.py             # 50 emission factors (CEA/DEFRA/EPA/IPCC)
│   │   │   ├── company.py             # Greenfield Manufacturing Pvt. Ltd.
│   │   │   ├── activity.py            # 24 months of activity data + anomalies
│   │   │   └── suppliers.py           # 15 suppliers
│   │   └── templates/
│   │       ├── brsr.html              # WeasyPrint templates
│   │       ├── gri.html
│   │       └── tcfd.html
│   ├── tests/
│   │   ├── unit/                      # services (calc, scenario, validator)
│   │   ├── integration/               # routers with test DB
│   │   └── fixtures/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── routes.tsx                 # react-router v6
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx          # emissions hero screen
│   │   │   ├── DataManagement.tsx
│   │   │   ├── Suppliers.tsx
│   │   │   ├── Scenarios.tsx
│   │   │   ├── Reports.tsx
│   │   │   ├── AuditLog.tsx
│   │   │   └── Settings.tsx
│   │   ├── features/                  # feature-sliced business logic
│   │   │   ├── emissions/             # hooks, components, types
│   │   │   ├── data-ingestion/
│   │   │   ├── suppliers/
│   │   │   ├── scenarios/
│   │   │   ├── anomalies/
│   │   │   └── reports/
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui primitives
│   │   │   ├── charts/                # Recharts wrappers (scope donut, trend, treemap)
│   │   │   ├── layout/                # Sidebar, TopBar, PeriodSelector
│   │   │   └── common/                # DataQualityDot, DrillDown, MethodologyTooltip
│   │   ├── lib/
│   │   │   ├── api.ts                 # typed fetch client
│   │   │   ├── queryClient.ts         # TanStack Query
│   │   │   └── formatters.ts          # tCO2e, INR, dates
│   │   ├── hooks/
│   │   └── styles/
│   │       └── globals.css            # Tailwind + theme (teal #0F766E)
│   ├── index.html
│   ├── tailwind.config.ts
│   ├── vite.config.ts
│   └── package.json
│
├── data/
│   └── carbonlens.db                  # SQLite (gitignored)
│
├── docs/
│   ├── ARCHITECTURE.md                # this file
│   └── ESG_Platform_Build_Prompt.md
│
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Backend Layering

Strict three-layer flow: `Router → Service → Repository/ORM`. Routers stay thin (parse, delegate, serialize). Business logic lives in services so it's unit-testable without HTTP. The DB layer exposes SQLAlchemy models + session — no raw SQL.

| Layer | Responsibility | Must NOT |
|---|---|---|
| `api/v1/*` | HTTP parsing, auth, validation, response shaping | Contain calculation or business rules |
| `services/*` | Domain logic (calc, anomaly, scenario, reports) | Import FastAPI or know about HTTP |
| `db/models/*` | Schema, relationships, constraints | Contain business logic |
| `schemas/*` | Pydantic DTOs for request/response | Leak ORM objects to clients |

---

## 4. Data Model (9 tables)

Matches the spec:

- `organizations` — tenant root
- `facilities` — factory/office/warehouse under an org
- `emission_factors` — DEFRA/EPA/IPCC/CEA factors, versioned by year/region
- `activity_data` — raw consumption events (scope, category, quantity, unit, period)
- `emissions` — computed CO2e per activity row (FK to both `activity_data` and `emission_factor`)
- `suppliers` — tier, maturity level, spend, scope3 category
- `supplier_submissions` — submitted data + review status
- `scenarios` — saved what-if runs (params JSON, projected emissions)
- `audit_log` — every mutation (old/new value, user, timestamp)
- `reports` — generated report artifacts (type, period, file path, status)

**Key invariant — Traceability chain:**
```
activity_data.id ──► emissions.activity_data_id
                     emissions.emission_factor_id ──► emission_factors.id
                     emissions.calculation_method (stored formula)
```
Every figure in a BRSR/GRI/TCFD report must resolve back through this chain. This *is* the "assurance-ready" requirement.

---

## 5. Module → Service Mapping

| Module | Services | Routers |
|---|---|---|
| 1. Data Ingestion | `validator`, `document_parser`, `audit` | `activity`, `uploads`, `audit` |
| 2. GHG Calculation | `calculation_engine` | `emissions`, `factors` |
| 3. Supplier Engagement | `supplier_scoring` | `suppliers` |
| 4A. Anomaly Detection | `anomaly_detector` | `anomalies` |
| 4B. Scenario Modeling | `scenario_engine` | `scenarios` |
| 5. Reports & Dashboards | `report_builder` | `reports`, `dashboards` |

---

## 6. Claude Integration

One wrapper — `core/claude_client.py` — with:

- Retry (exponential backoff, max 3)
- Circuit breaker (open after 5 consecutive failures, half-open after 60s)
- Token/cost logging
- Prompt templates in `services/prompts/` (one file per use case)

**Graceful degradation:** every caller must handle `ClaudeUnavailable`:

| Feature | Claude available | Claude unavailable |
|---|---|---|
| Document parser | Structured extraction | Return form for manual entry |
| Anomaly explanation | AI narrative + severity | Statistical severity only, generic text |
| Scenario narrative | 2–3 paragraph strategy | Hide narrative panel, show chart only |
| Report narratives | AI governance/strategy copy | Boilerplate template text |

---

## 7. Frontend Architecture

- **Feature-sliced** under `src/features/*` — each feature owns its API hooks, components, and types. Pages compose features.
- **TanStack Query** for server state — caching, invalidation on mutation, optimistic updates for data entry.
- **shadcn/ui + Tailwind** — primitives copied into `components/ui/`; theme via CSS variables (primary teal `#0F766E`).
- **Recharts** wrapped in `components/charts/` so chart choices stay swappable.
- **Reusable UX primitives** (mandated by spec):
  - `<DataQualityDot level="verified|estimated|flagged" />`
  - `<DrillDown onClick={…}>` wraps any number to open source data
  - `<MethodologyTooltip factor={…} method={…} />`
  - `<ViewDataToggle />` on every chart
- **Period context** — global `PeriodSelector` stored in a React context; all queries key off `(orgId, periodStart, periodEnd)`.

---

## 8. Calculation Engine (Module 2)

Pure function per record:

```
emission_kg = activity.quantity × factor.factor_value × unit_conversion
```

Resolution order for factor matching:
1. Exact: `category + subcategory + region + year`
2. Fallback: `category + subcategory + region` (most recent year)
3. Fallback: `category + subcategory` (global)
4. If none → flag activity as `UNRESOLVED`, do not silently pick a wrong factor.

Scope-specific methods:
- **Scope 1:** direct fuel × factor
- **Scope 2:** location-based (grid factor) AND market-based (if RE certs exist)
- **Scope 3:** activity-based if data present, spend-based fallback (spend × spend-factor)

Every `emissions` row stores the `calculation_method` string so the UI can render the exact formula used.

---

## 9. Scenario Engine (Module 4B)

Pure, deterministic function:

```python
def project(baseline: Emissions, levers: Levers, target_year: int) -> Trajectory
```

No DB writes during slider interaction — only when user clicks "Save Scenario". Levers from spec: renewable %, fleet electrification %, efficiency %, supplier engagement N, carbon price. Output: year-by-year trajectory + gap-to-net-zero + financial exposure. Claude is called *after* computation to generate the narrative — the math never depends on the LLM.

---

## 10. Anomaly Detection (Module 4A)

Two-stage pipeline:

1. **Statistical pass (deterministic):** rolling mean + stddev per `(facility, category)`. Flag: >2σ deviation, zero values, missing periods, sudden spikes >50% MoM.
2. **Explanation pass (Claude):** for each flagged anomaly, Claude returns `{severity, likely_cause, recommended_action, confidence}`. Cached per anomaly — never re-called unless the underlying data changes.

---

## 11. Report Generation (Module 5)

- Jinja2 HTML templates per framework (BRSR, GRI, TCFD) → WeasyPrint → PDF.
- Charts rendered server-side via Matplotlib and embedded as PNG (so PDF is self-contained).
- Every number in the report carries an invisible marker (`data-source-id`) linking to its `emissions.id` for audit trail export.
- Claude fills narrative sections only; all numbers come from the DB.

---

## 12. Audit & Traceability

- `services/audit.py` is called from every mutation (create/update/delete) in every service.
- `audit_log` stores `{user, action, entity_type, entity_id, old_value, new_value, timestamp}`.
- UI: searchable log viewer at `/audit` with entity-type filter.
- Reports embed a methodology appendix auto-generated from the audit log.

---

## 13. Configuration & Environments

`.env` (via `pydantic-settings`):

```
DATABASE_URL=sqlite:///./data/carbonlens.db
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514
CORS_ORIGINS=http://localhost:5173
PDF_OUTPUT_DIR=./data/reports
LOG_LEVEL=INFO
```

SQLite → Postgres swap: change `DATABASE_URL` only. No code changes.

---

## 14. Build Order (maps to spec)

1. DB schema + Alembic + seed (Greenfield Mfg., 50 factors, 24 months activity)
2. Calculation engine + `/api/calculate` + factor matching
3. Frontend shell (sidebar, top bar, period selector, routing)
4. Emissions Dashboard (hero screen — donut, trend, facility bars, quality indicator)
5. Data Management (manual entry, CSV upload, validation)
6. AI Document Parser (Claude integration #1)
7. Supplier Portal (registry, impact matrix, submission workflow)
8. Anomaly Detection (stats + Claude explanation)
9. Scenario Simulator (levers, trajectory chart, narrative)
10. Report Generation (BRSR → GRI → TCFD)
11. Governance Dashboards (exec + ops views)
12. Audit Trail UI

---

## 15. Non-Goals (v1)

- Multi-tenancy / auth (demo is single-org; design keeps `org_id` on every table for later)
- Real supplier email/notifications (in-app simulation only, per spec)
- Real-time streaming (batch-oriented is fine for ESG cadence)
- Mobile-first layouts (desktop-first enterprise tool)
