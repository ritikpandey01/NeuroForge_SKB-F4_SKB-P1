# Supplier Submissions — copy-paste values

Open `http://localhost:5174/suppliers` → **Submit data** tab. Pick a supplier from the dropdown, then fill the form.

> The submission lands as **status=pending**. To accept/flag/reject it, hit the registry tab and use the review action.

---

### Submission A — SteelCorp India (Q1 2025) · realistic

| Field | Value |
|---|---|
| Supplier | `SteelCorp India` |
| Period | `2025-Q1` |
| Total emissions | `4280` tCO₂e |
| Scope 1 | `1240` |
| Scope 2 | `2810` |
| Scope 3 | `230` |
| Methodology | `Spend-based (EXIOBASE) cross-checked with supplier-specific factor` |
| Verification status | `unverified` |
| Notes | `Q1 2025 figures based on actual production volumes — final audit pending June.` |

---

### Submission B — Precision Parts Co (Q1 2025) · improved methodology

| Field | Value |
|---|---|
| Supplier | `Precision Parts Co` |
| Period | `2025-Q1` |
| Total emissions | `185` tCO₂e |
| Scope 1 | `42` |
| Scope 2 | `128` |
| Scope 3 | `15` |
| Methodology | `Activity-based (electricity meter readings + diesel logs)` |
| Verification status | `third_party_verified` |
| Notes | `Switched from spend-based to activity-based reporting this quarter.` |

---

### Submission C — INTENTIONAL ANOMALY · zero-value report

This will trigger the zero-value detector when you next run an anomaly scan.

| Field | Value |
|---|---|
| Supplier | `CopperLine Industries` |
| Period | `2025-Q1` |
| Total emissions | **`0`** ← implausible |
| Scope 1 | `0` |
| Scope 2 | `0` |
| Scope 3 | `0` |
| Methodology | `(blank)` |
| Verification status | `unverified` |
| Notes | `Submission incomplete — supplier did not provide actual numbers.` |

After saving: `/anomalies` → **Run scan** → new "Zero-value supplier submission" should appear.
