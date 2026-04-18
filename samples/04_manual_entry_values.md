# Manual Entry — copy-paste values

Open `http://localhost:5174/data` → **Manual entry** tab. Use any of these:

---

### Example 1 — Pune electricity (April 2025)

| Field | Value |
|---|---|
| Facility | `Pune Factory` |
| Scope | `2` |
| Category | `electricity` |
| Subcategory | `grid_india` |
| Activity description | `MSEDCL grid electricity - main feeder` |
| Quantity | `175,200` |
| Unit | `kWh` |
| Period start | `2025-04-01` |
| Period end | `2025-04-30` |
| Source document | `MSEDCL-INV-202504-PUN` |
| Data quality | `5` |

Expected emissions: ~143.8 tCO₂e (Indian grid factor ≈ 0.82 kg/kWh)

---

### Example 2 — Chennai DG diesel (April 2025)

| Field | Value |
|---|---|
| Facility | `Chennai Factory` |
| Scope | `1` |
| Category | `fuel` |
| Subcategory | `diesel` |
| Activity description | `DG set diesel - 250 kVA backup` |
| Quantity | `4,500` |
| Unit | `litre` |
| Period start | `2025-04-01` |
| Period end | `2025-04-30` |
| Source document | `IOCL-RB-202504-CHN` |
| Data quality | `5` |

Expected emissions: ~12.0 tCO₂e (diesel ≈ 2.68 kg/L)

---

### Example 3 — Mumbai office travel (April 2025)

| Field | Value |
|---|---|
| Facility | `Mumbai Corporate Office` |
| Scope | `3` |
| Category | `travel` |
| Subcategory | `flight_domestic` |
| Activity description | `Mumbai-Bangalore sales team flights` |
| Quantity | `22,400` |
| Unit | `passenger-km` |
| Period start | `2025-04-01` |
| Period end | `2025-04-30` |
| Source document | `CONCUR-EXP-202504` |
| Data quality | `3` |

Expected emissions: ~3.6 tCO₂e

---

### Example 4 — INTENTIONAL ANOMALY (to test the detector)

Enter this and then run a scan on `/anomalies` — it should fire as a z-score outlier:

| Field | Value |
|---|---|
| Facility | `Pune Factory` |
| Scope | `2` |
| Category | `electricity` |
| Subcategory | `grid_india` |
| Activity description | `MSEDCL grid electricity - main feeder` |
| Quantity | **`540,000`** ← 3× normal |
| Unit | `kWh` |
| Period start | `2025-05-01` |
| Period end | `2025-05-31` |
| Source document | `MSEDCL-INV-202505-PUN` |
| Data quality | `5` |

After saving: go to `/anomalies` → click **Run scan** → a new "Outlier in Pune Factory · grid_india" should appear (severity high). Then test the **Escalate to board** button.
