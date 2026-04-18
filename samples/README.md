# CarbonLens — Sample Test Data

End-to-end test fixtures for every ingestion path in the app. Frontend at `http://localhost:5174`, backend at `:8000`.

## Files in this folder

| # | File | What it tests | Where to upload |
|---|---|---|---|
| 1 | `01_electricity_pune_q1_2025.csv` | CSV upload — 6 rows, Scope 2 grid + solar PPA | `/data` → CSV upload |
| 2 | `02_diesel_chennai_q1_2025.csv` | CSV upload — 7 rows, Scope 1 fuels (diesel, gas, LPG) | `/data` → CSV upload |
| 3 | `03_mixed_january_2025.csv` | CSV upload — 9 rows, all 3 scopes mixed (steel, freight, travel, refrigerant) | `/data` → CSV upload |
| 4 | `04_manual_entry_values.md` | Copy-paste values for the Manual entry form, including 1 intentional anomaly | `/data` → Manual entry |
| 5 | `05_supplier_submissions.md` | 3 sample supplier submissions inc. 1 intentional zero-value anomaly | `/suppliers` → Submit data |
| 6 | `bills/electricity_bill_pune_jan2025.pdf` | AI parser · Scope 2 · MSEDCL HT industrial (Maharashtra) | `/data` → Document parse (AI) |
| 7 | `bills/electricity_bill_mumbai_feb2025.pdf` | AI parser · Scope 2 · BEST commercial (Mumbai LT-II) | `/data` → Document parse (AI) |
| 8 | `bills/diesel_invoice_chennai_feb2025.pdf` | AI parser · Scope 1 · IOCL bulk diesel (3 deliveries) | `/data` → Document parse (AI) |
| 9 | `bills/natural_gas_bill_chennai_mar2025.pdf` | AI parser · Scope 1 · GAIL PNG industrial | `/data` → Document parse (AI) |
| 10 | `bills/steel_invoice_jsw_apr2025.pdf` | AI parser · Scope 3 · JSW hot-rolled coil (620 MT) | `/data` → Document parse (AI) |
| 11 | `bills/freight_invoice_gati_apr2025.pdf` | AI parser · Scope 3 · Gati surface freight (4 LRs) | `/data` → Document parse (AI) |
| 12 | `bills/flight_itinerary_indigo_mar2025.pdf` | AI parser · Scope 3 · IndiGo 3-segment corporate itinerary | `/data` → Document parse (AI) |
| 13 | `bills/waste_disposal_chennai_feb2025.pdf` | AI parser · Scope 3 · Ramky waste disposal (4 streams) | `/data` → Document parse (AI) |

## Suggested test order (15 min walkthrough)

1. **CSV upload (manual review path)**
   - `/data` → CSV upload tab → drop `01_electricity_pune_q1_2025.csv`
   - Preview shows 6 rows, no errors. Click **Commit**.
   - Repeat with files 2 and 3.
   - Result: 22 new activity rows, ~22 new emission calculations.

2. **AI document parser**
   - `/data` → Document parse (AI) tab → drop `bills/electricity_bill_pune_jan2025.pdf`
   - Wait ~10s. The parser should extract a row matching:
     - facility=Pune Factory, scope=2, category=electricity, subcategory=grid_india, quantity=182,400, unit=kWh, period=Jan 2025
   - Review the preview, then **Commit**. (NB: this is the *same* row as in CSV #1 — the system will likely create a duplicate. That's expected — humans review before commit.)
   - Repeat with the diesel and natural gas bills.

3. **Manual entry**
   - `/data` → Manual entry → use any example from `04_manual_entry_values.md`
   - Try Example 4 (the 540,000 kWh anomaly) so the detector has something to find.

4. **Supplier portal**
   - `/suppliers` → Submit data tab → use Submission A from `05_supplier_submissions.md`
   - Then Submission C (the zero-value anomaly).
   - Switch to Registry tab → click the new pending submissions to **review** → accept/flag/reject.

5. **Run anomaly scan**
   - `/anomalies` → click **Run scan**
   - Should find the 540,000 kWh outlier (z-score) AND the zero-value supplier submission.
   - On the high-severity outlier, click **Escalate to board** → fill owner + due date + notes.
   - On a still-escalated row, click **Mark as reviewed** to close the loop.

6. **Generate a report**
   - `/reports` → Framework=BRSR, Period=`FY2024`, Include AI narrative=on
   - Wait ~3-5s → row appears with status=ready → click **PDF** to download.

7. **Audit log**
   - `/audit-log` → should show every action above (csv_commit, activity.created, supplier_submission.reviewed, anomaly.escalated, anomaly.board_reviewed, report.generated).

## Regenerating the PDF bills

If you want to tweak the layout or values:

```bash
backend/.venv/bin/python samples/bills/generate_bills.py
```

Edits live in `samples/bills/generate_bills.py`. ReportLab v4.

## What the data is modeled on

- **Electricity bill** — MSEDCL HT-I industrial tariff format. Real consumer numbers + tariff slabs for Pune circle.
- **Diesel invoice** — IOCL bulk supply format (DC-numbered tanker deliveries, BS-VI HSD pricing).
- **Natural gas bill** — GAIL PNG industrial format with calorific-value adjustment.
- **Numbers are plausible for a 50-100 MW-class auto-component plant** — based on public benchmarks, not a specific company.
- **Greenfield Manufacturing** is the seeded demo tenant. Replace with your real org in production.
