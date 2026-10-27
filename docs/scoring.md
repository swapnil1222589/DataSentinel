# DataSentinel Quality Scoring Methodology

DataSentinel calculates a transparent, deterministic **Data Quality Score** ranging from **0.0 to 100.0**, mapped to an academic letter grade (A+ through F).

> [!NOTE]
> **Heuristic Notice:** The DataSentinel Quality Score is an automated heuristic designed to highlight structural deficiencies and distribution anomalies. It is not an absolute standard; domain requirements should always govern dataset acceptance.

---

## Dimensions and Default Weights

The overall score is a normalized weighted average of four core data quality dimensions:

$$\text{Overall Score} = w_c \cdot S_{\text{comp}} + w_v \cdot S_{\text{val}} + w_u \cdot S_{\text{uniq}} + w_s \cdot S_{\text{cons}}$$

Where $\sum w_i = 1.0$.

| Dimension | Default Weight ($w_i$) | Scope & Definition |
| :--- | :---: | :--- |
| **Completeness** ($S_{\text{comp}}$) | **35%** | Evaluates the absence of missing cells, nulls, and disguised placeholder values. |
| **Validity** ($S_{\text{val}}$) | **30%** | Measures adherence to schema constraints, custom domain rules, and correct data types. |
| **Uniqueness** ($S_{\text{uniq}}$) | **20%** | Evaluates the absence of redundant records and exact duplicate rows. |
| **Consistency** ($S_{\text{cons}}$) | **15%** | Evaluates internal dataset uniformity, clean string whitespace, and lack of zero-variance columns. |

---

## Detailed Formulas and Deductions

### 1. Completeness Score ($S_{\text{comp}}$)
Starts at **100.0** points:
- **Missing Cell Penalty:** Bounded deduction based on overall missing rate:
  $$\Delta_{\text{missing}} = \min(80.0, \, \text{Missing Cell Rate} \times 1.5)$$
- **Empty Column Penalty:** Each completely empty (100% null) column incurs a **10.0 point deduction** (capped at 40.0 points).
- **Result:** $S_{\text{comp}} = \max(0.0, \, 100.0 - \Delta_{\text{missing}} - \Delta_{\text{empty\_cols}})$.

### 2. Uniqueness Score ($S_{\text{uniq}}$)
Starts at **100.0** points:
- **Duplicate Rows Penalty:** Proportional deduction based on percentage of redundant duplicate rows:
  $$\Delta_{\text{dup}} = \min(90.0, \, \text{Duplicate Row Rate} \times 2.5)$$
- **Result:** $S_{\text{uniq}} = \max(0.0, \, 100.0 - \Delta_{\text{dup}})$.

### 3. Validity Score ($S_{\text{val}}$)
Starts at **100.0** points:
- **Custom Rule Failures:** Deducts between 5.0 and 25.0 points per failed rule depending on violation rate:
  $$\Delta_{\text{rule}} = \min(25.0, \, \max(5.0, \, \text{Violation Rate} \times 0.4))$$
- **Mixed Data Types:** 8.0 points per column containing incompatible Python types.
- **Numbers Stored as Text:** 5.0 points per text column that contains parseable numbers.
- **Result:** $S_{\text{val}} = \max(0.0, \, 100.0 - \sum \Delta_{\text{val}})$.

### 4. Consistency Score ($S_{\text{cons}}$)
Starts at **100.0** points:
- **Constant Columns (Zero Variance):** 5.0 points deduction per constant column.
- **Duplicate Identical Columns:** 8.0 points deduction per redundant pair.
- **Untrimmed Whitespace:** 4.0 points deduction per column with leading/trailing spaces.
- **Result:** $S_{\text{cons}} = \max(0.0, \, 100.0 - \sum \Delta_{\text{cons}})$.

---

## Safety Guardrail: Critical Issue Cap

A high overall score should never conceal catastrophic single-column failures.

If **any CRITICAL severity issue** is detected (e.g. a column is 100% empty, or an essential domain rule has extreme violation), the overall score is **strictly capped at 65.0** (Grade D).

---

## Letter Grade Boundaries

| Score Range | Grade | Interpretation |
| :---: | :---: | :--- |
| **95.0 – 100.0** | **A+** | Exemplary quality; ready for mission-critical ML and analytics. |
| **90.0 – 94.9** | **A** | Excellent quality; minor cosmetic notices. |
| **80.0 – 89.9** | **B** | Good quality; moderate missingness or minor schema warnings. |
| **70.0 – 79.9** | **C** | Mediocre quality; noticeable duplicates, untrimmed strings, or mild rule violations. |
| **60.0 – 69.9** | **D** | Poor quality; significant missingness or presence of Critical issue cap. |
| **< 60.0** | **F** | Unacceptable quality; severe structural defects, widespread corruption, or empty dataset. |
