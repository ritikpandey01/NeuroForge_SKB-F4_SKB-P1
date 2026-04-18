# BUILD PROMPT: Digital Intelligent Platform for ESG Performance & GHG Monitoring

## PROJECT OVERVIEW

Build a full-stack web application called **"CarbonLens"** — a Digital Intelligent Platform for ESG Performance and GHG Monitoring. This is a centralized enterprise platform that allows organizations to measure, track, analyze, and report their Greenhouse Gas (GHG) emissions across Scope 1, 2, and 3, engage suppliers for better data quality, run AI-powered climate scenario analysis, and auto-generate assurance-ready sustainability reports.

The platform must demonstrate 5 core capabilities:
1. Centralized data ingestion and management
2. GHG emissions calculation engine (Scope 1, 2, 3)
3. Supplier engagement and data quality scoring
4. AI-powered analytics, anomaly detection, and scenario modeling
5. Governance dashboards and auto-generated sustainability reports

---

## TECH STACK

- **Frontend**: React (Vite) + Tailwind CSS + shadcn/ui components + Recharts for charts
- **Backend**: Python FastAPI
- **Database**: SQLite (for demo simplicity, structured to be swappable to PostgreSQL)
- **AI/LLM**: Anthropic Claude API (claude-sonnet-4-20250514) — used for document parsing, anomaly explanation, scenario narrative generation, and transition pathway reports
- **PDF Reports**: ReportLab or WeasyPrint
- **File Parsing**: pandas for CSV/Excel, pdfplumber or PyMuPDF for PDF text extraction before sending to LLM

---

## DATABASE SCHEMA

Design the following tables:

### `organizations`
- id, name, industry, country, base_year, net_zero_target_year, created_at

### `facilities`
- id, org_id (FK), name, type (factory/office/warehouse), location, country, created_at

### `emission_factors`
- id, category (electricity/fuel/travel/material), subcategory, factor_value, unit (kgCO2e per unit), source (DEFRA/EPA/IPCC), region, year

### `activity_data`
- id, facility_id (FK), scope (1/2/3), category, subcategory, activity_description, quantity, unit, period_start, period_end, source_document, data_quality_score (1-5), verified (boolean), uploaded_by, created_at, updated_at

### `emissions`
- id, activity_data_id (FK), scope, category, co2e_kg, calculation_method, emission_factor_id (FK), created_at

### `suppliers`
- id, org_id (FK), name, industry, country, contact_email, tier (1/2/3), data_maturity_level (spend_based / activity_based / verified_primary), scope3_category, annual_spend, created_at

### `supplier_submissions`
- id, supplier_id (FK), period, submitted_data (JSON), data_quality_score, status (pending/accepted/flagged/rejected), submitted_at, reviewed_at

### `scenarios`
- id, org_id (FK), name, description, parameters (JSON), baseline_emissions, projected_emissions, created_by, created_at

### `audit_log`
- id, org_id (FK), user, action, entity_type, entity_id, old_value, new_value, timestamp

### `reports`
- id, org_id (FK), report_type (BRSR/GRI/TCFD/CDP), period, generated_at, file_path, status

---

## SEED DATA

Create a realistic fictional company for demo purposes:

**Company: Greenfield Manufacturing Pvt. Ltd.**
- Industry: Auto Components Manufacturing
- Country: India
- 3 Facilities: Pune Factory, Chennai Factory, Mumbai Corporate Office
- Base Year: 2022
- Net Zero Target: 2045
- ~15 suppliers across 4 Scope 3 categories

### Seed the following data:

**Emission Factors (pre-load ~50 common factors):**
- India grid electricity: 0.716 kgCO2e/kWh (CEA 2023)
- Diesel: 2.68 kgCO2e/litre
- Petrol: 2.31 kgCO2e/litre
- Natural gas: 2.02 kgCO2e/m³
- Domestic flight: 0.255 kgCO2e/passenger-km
- International flight: 0.195 kgCO2e/passenger-km
- Hotel night: 20 kgCO2e/night
- Steel: 1.85 kgCO2e/kg
- Aluminium: 8.24 kgCO2e/kg
- Plastics (general): 3.12 kgCO2e/kg
- Road freight: 0.107 kgCO2e/tonne-km
- Employee commute (car): 0.17 kgCO2e/km
- Paper: 0.91 kgCO2e/kg
- Water supply: 0.344 kgCO2e/m³
- Waste to landfill: 0.586 kgCO2e/kg

**Activity Data (24 months: Jan 2024 – Dec 2025):**

Scope 1:
- Diesel for DG sets (Pune): 3000-5000 litres/month (seasonal variation, higher in summer)
- Natural gas for furnace (Chennai): 8000-12000 m³/month
- Company fleet diesel (all facilities): 1500-2500 litres/month
- Refrigerant top-ups: R-410A, 15kg per quarter (GWP: 2088)

Scope 2:
- Electricity (Pune Factory): 150,000-220,000 kWh/month
- Electricity (Chennai Factory): 120,000-180,000 kWh/month
- Electricity (Mumbai Office): 25,000-35,000 kWh/month

Scope 3:
- Cat 1 (Purchased Goods): Steel 500-800 tonnes/month, Aluminium 50-100 tonnes/month, Plastics 30-60 tonnes/month
- Cat 4 (Upstream Transport): 200,000-400,000 tonne-km/month by road
- Cat 6 (Business Travel): 15-30 domestic flights/month, 2-5 international flights/month, 30-60 hotel nights/month
- Cat 7 (Employee Commute): 850 employees, avg 15km one-way, 22 working days/month

**Add intentional data anomalies for AI detection:**
- One month with electricity 3x normal (data entry error)
- One supplier reporting zero emissions for a quarter
- A sudden spike in diesel consumption in one month
- Missing data for one facility for 2 months

**Suppliers (15 suppliers):**

| Name | Category | Tier | Maturity | Annual Spend (₹ Cr) |
|---|---|---|---|---|
| SteelCorp India | Purchased Goods - Steel | 1 | activity_based | 45 |
| MetalWorks Ltd | Purchased Goods - Aluminium | 1 | spend_based | 12 |
| PolyPack Solutions | Purchased Goods - Plastics | 2 | spend_based | 8 |
| FastFreight Logistics | Upstream Transport | 1 | activity_based | 15 |
| RoadHaul Express | Upstream Transport | 2 | spend_based | 6 |
| Precision Parts Co | Purchased Goods - Components | 1 | verified_primary | 22 |
| (+ 9 more with varying maturity levels and spend) | | | | |

---

## MODULE 1: DATA INGESTION & MANAGEMENT

### Features:
1. **Manual Entry Forms**: Structured forms for each scope/category with dropdowns for units, facility selection, period selection
2. **CSV/Excel Upload**: Upload bulk activity data via CSV template. Validate columns, flag errors, preview before import
3. **AI Document Parser**: Upload a utility bill, fuel receipt, or invoice as PDF/image. Use Claude API to extract:
   - Vendor/provider name
   - Billing period
   - Consumption quantity and unit
   - Cost
   - Facility (if identifiable)
   Return structured JSON, let user confirm/edit before saving
4. **Data Validation**: Flag entries that deviate >2 standard deviations from historical average for that category/facility
5. **Audit Trail**: Every create/update/delete is logged with old value, new value, user, timestamp

### API Endpoints:
- `POST /api/activity-data` — create entry
- `PUT /api/activity-data/{id}` — update entry
- `GET /api/activity-data?scope=&facility=&period=` — list with filters
- `POST /api/upload/csv` — bulk upload
- `POST /api/upload/document` — AI-powered document parsing
- `GET /api/audit-log?entity=` — audit trail

### AI Document Parsing Prompt:
```
You are an ESG data extraction assistant. Extract the following fields from this document:
- document_type (utility_bill / fuel_receipt / invoice / travel_booking)
- vendor_name
- billing_period_start (YYYY-MM-DD)
- billing_period_end (YYYY-MM-DD)
- line_items: array of { description, quantity, unit, cost, currency }
- facility_hint (any location/address info that could map to a facility)

Return ONLY valid JSON. No explanation.
```

---

## MODULE 2: GHG CALCULATION ENGINE

### Features:
1. **Automatic Calculation**: When activity data is saved, auto-calculate emissions by matching to the appropriate emission factor
2. **Methodology Support**:
   - Scope 1: Direct measurement (fuel quantity × emission factor)
   - Scope 2: Location-based (kWh × grid factor) and market-based (if RE certificates available)
   - Scope 3: Activity-based where data exists, spend-based (spend × spend-based factor) as fallback
3. **Emission Factor Library**: Pre-loaded, searchable, with source attribution and year
4. **Calculation Transparency**: Every emission record links back to the activity data AND the emission factor used, with full formula shown

### API Endpoints:
- `POST /api/calculate` — trigger calculation for a batch of activity data
- `GET /api/emissions/summary?scope=&period=&facility=` — aggregated emissions
- `GET /api/emissions/{id}/methodology` — show calculation breakdown
- `GET /api/emission-factors?category=&region=` — browse factors

### Dashboard View:
- **Total emissions** (tCO2e) with period-over-period change
- **Scope 1 / 2 / 3 donut chart** with drill-down
- **Monthly emissions trend** (stacked bar by scope)
- **Facility-wise comparison** (horizontal bar chart)
- **Top 5 emission categories** (ranked bar)
- **Scope 3 category breakdown** (treemap or bar)
- **Data quality indicator** — % of data that is verified vs estimated

---

## MODULE 3: SUPPLIER ENGAGEMENT PORTAL

### Features:
1. **Supplier Registry**: List all suppliers with tier, maturity level, Scope 3 category, annual spend, data quality score
2. **Supplier Dashboard**: Show which suppliers are highest-impact (spend × emission intensity), prioritize engagement
3. **Data Request Workflow**:
   - Generate data request for a supplier (what data is needed, for which period, in what format)
   - Supplier submits data via a simple form (simulate this in the app — no need for actual email/auth)
   - Review submitted data, accept/flag/reject
4. **Maturity Scoring**:
   - Level 1 (Spend-based): Only spend data available, emissions estimated using spend-based factors
   - Level 2 (Activity-based): Supplier provides activity data (kWh, fuel, materials) but unverified
   - Level 3 (Verified Primary): Supplier provides verified emissions data with third-party assurance
5. **Progress Tracking**: Show maturity improvement over time, % of Scope 3 covered by primary data

### API Endpoints:
- `GET /api/suppliers?tier=&maturity=` — list suppliers
- `POST /api/suppliers/{id}/request-data` — send data request
- `POST /api/suppliers/{id}/submit` — supplier submits data
- `PUT /api/suppliers/{id}/review` — review submission
- `GET /api/suppliers/impact-matrix` — spend vs emissions matrix

---

## MODULE 4: AI-POWERED ANALYTICS & SCENARIO MODELING

### Feature 4A: Anomaly Detection
- Scan all activity data and emissions for statistical anomalies (>2σ deviation, zero values, missing periods, sudden spikes/drops)
- Use Claude API to generate **plain English explanations** of each anomaly and suggested actions
- Display as an alert feed with severity (high/medium/low)

**Anomaly Detection Prompt:**
```
You are a GHG emissions data quality analyst. Given the following anomaly:

Facility: {facility}
Category: {category}
Period: {period}
Reported Value: {value} {unit}
Historical Average: {avg} {unit}
Standard Deviation: {std}
Deviation: {deviation_factor}x

Provide:
1. severity: high / medium / low
2. likely_cause: one sentence
3. recommended_action: one sentence
4. confidence: 0-100

Return ONLY valid JSON.
```

### Feature 4B: Scenario Simulator
Interactive interface where user can:
- Set a base year and target year
- Toggle levers:
  - "Switch X% of electricity to renewable" (slider 0-100%)
  - "Electrify X% of fleet" (slider 0-100%)
  - "Improve energy efficiency by X%" (slider 0-30%)
  - "Engage top N suppliers to provide primary data" (slider)
  - "Carbon price ($/tCO2e)" (slider 0-200)
- Show a **projected emissions trajectory chart** (line chart, base case vs scenario)
- Show **financial impact** (carbon cost exposure, investment needed)
- Use Claude API to generate a **Transition Pathway Narrative** — a 2-3 paragraph strategic summary of what the scenario means and recommended actions

**Scenario Narrative Prompt:**
```
You are a climate strategy advisor. Given the following scenario analysis for {company_name}:

Base Year Emissions: {base_emissions} tCO2e
Current Year Emissions: {current_emissions} tCO2e
Target: Net Zero by {target_year}

Scenario Parameters:
- Renewable electricity: {renewable_pct}%
- Fleet electrification: {fleet_pct}%
- Energy efficiency improvement: {efficiency_pct}%
- Supplier engagement: Top {supplier_count} suppliers targeted
- Carbon price assumption: ${carbon_price}/tCO2e

Projected Emissions in Target Year: {projected_emissions} tCO2e
Gap to Net Zero: {gap} tCO2e
Estimated Carbon Cost Exposure: ${carbon_cost}

Write a 2-3 paragraph transition pathway narrative that:
1. Summarizes the scenario outcome
2. Identifies the biggest levers for reduction
3. Highlights risks and recommends next steps
4. Uses a professional, boardroom-ready tone

Do NOT use bullet points. Write in flowing paragraphs.
```

### API Endpoints:
- `GET /api/anomalies` — list detected anomalies with AI explanations
- `POST /api/scenarios` — create and run a scenario
- `GET /api/scenarios/{id}` — get scenario results
- `POST /api/scenarios/{id}/narrative` — generate AI narrative

---

## MODULE 5: GOVERNANCE DASHBOARDS & REPORT GENERATION

### Feature 5A: Role-Based Dashboards

**Executive/Board View:**
- Total emissions (Scope 1+2+3) with YoY trend
- Net zero progress tracker (% reduction from base year, trajectory vs target)
- Top risks: regulatory exposure, carbon price impact, non-compliant suppliers
- ESG score/rating (simplified composite score)
- Escalation alerts (data quality below threshold, missed targets, supplier non-response)

**Operations View:**
- Facility-level granular data
- Category-wise breakdown with drill-down
- Data completeness tracker (% of expected data received)
- Pending actions (supplier follow-ups, data validation, anomaly resolution)

### Feature 5B: Auto-Generated Reports

Generate PDF sustainability reports in the following frameworks:

**BRSR (Business Responsibility and Sustainability Report):**
- Principle 6: Environment
  - Energy consumption (total, renewable vs non-renewable)
  - GHG emissions (Scope 1, 2, 3)
  - Water consumption
  - Waste generated
- Auto-fill data from the platform
- Include methodology notes and data quality disclaimers

**GRI (Global Reporting Initiative):**
- GRI 305-1: Direct GHG emissions (Scope 1)
- GRI 305-2: Energy indirect GHG emissions (Scope 2)
- GRI 305-3: Other indirect GHG emissions (Scope 3)
- GRI 305-4: GHG emissions intensity
- GRI 305-5: Reduction of GHG emissions

**TCFD (Task Force on Climate-related Financial Disclosures):**
- Governance section
- Strategy section (with scenario analysis results)
- Risk Management section
- Metrics & Targets section

For each report:
- Pull data directly from the emissions database
- Use Claude API to generate narrative sections (governance description, strategy commentary)
- Include charts as embedded images in PDF
- Add audit trail summary (data sources, methodology, verification status)
- Generate as downloadable PDF

### API Endpoints:
- `GET /api/dashboard/executive` — executive KPIs
- `GET /api/dashboard/operations?facility=` — operational metrics
- `POST /api/reports/generate` — generate report (type, period)
- `GET /api/reports/{id}/download` — download PDF
- `GET /api/escalations` — active escalation alerts

---

## UI/UX REQUIREMENTS

### Layout:
- **Sidebar navigation**: Dashboard, Data Management, Emissions, Suppliers, Scenarios, Reports, Settings
- **Top bar**: Organization name, period selector (FY 2024-25, FY 2025-26), user role indicator
- **Color scheme**: Professional, clean. Primary: deep teal (#0F766E). Accent: amber for warnings, red for alerts, green for positive trends. Dark mode support optional.

### Key UX Principles:
- Every number should be clickable to drill down to its source data
- Every chart should have a "View Data" toggle to see the underlying table
- Show calculation methodology inline (tooltip or expandable section)
- Data quality indicators everywhere (colored dots: green=verified, yellow=estimated, red=flagged)
- Loading states and empty states for all views
- Responsive but desktop-first (this is an enterprise tool)

---

## IMPLEMENTATION ORDER

Build in this sequence:
1. **Database + Seed Data** — Set up schema, seed all demo data
2. **Backend API** — All CRUD endpoints, calculation engine, emission factor matching
3. **Frontend Shell** — Sidebar, routing, layout, period selector
4. **Emissions Dashboard** (Module 2 dashboard) — This is the hero screen
5. **Data Management** (Module 1) — Upload, manual entry, validation
6. **AI Document Parser** (Module 1) — Claude API integration for document extraction
7. **Supplier Portal** (Module 3) — Registry, maturity scoring, submission workflow
8. **Anomaly Detection** (Module 4A) — Statistical detection + AI explanation
9. **Scenario Simulator** (Module 4B) — Interactive levers + trajectory chart + AI narrative
10. **Report Generation** (Module 5) — PDF generation for BRSR/GRI/TCFD
11. **Governance Dashboards** (Module 5A) — Executive and operations views
12. **Audit Trail UI** — Searchable audit log viewer

---

## CRITICAL NOTES

- **Every emission value must be traceable**: activity data → emission factor → calculated emission → report line item. This traceability IS the "assurance-ready" requirement.
- **All AI features should have graceful fallbacks**: If Claude API is down, the platform should still work — just without AI narratives/parsing.
- **Use realistic numbers**: The seed data should produce total emissions in the range of 15,000-25,000 tCO2e/year for this type of company. Scope 3 should be ~60-70% of total.
- **Indian context matters**: Use Indian grid emission factors (CEA), mention BRSR (SEBI mandate), use INR for spend data, reference Indian regulatory landscape.
