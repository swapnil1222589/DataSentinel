<div align="center">

# ⛨ DataSentinel

### Production-Quality Open-Source Data Quality & Observability Platform

**"Know your data before your model does."** 

[![CI](https://github.com/DataSentinel-ai/datasentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/DataSentinel-ai/datasentinel/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Privacy: 100% Offline](https://img.shields.io/badge/privacy-100%25%20offline-success)](docs/security.md)

</div>

---

## 📌 Overview

**DataSentinel** is an open-source, local-first dataset quality, validation, and observability platform built for data scientists, machine-learning engineers, developers, and analytics teams.

Before passing datasets into analytics dashboards, predictive ML models, or ETL pipelines, DataSentinel automatically inspects your tabular data to surface **missingness**, **duplicate records**, **type corruption**, **statistical distribution drift**, **outliers**, and **custom business rule violations**.

### Why DataSentinel?

- 🔒 **100% Local & Offline:** Operates entirely within your environment. Zero telemetry, zero external AI dependencies, zero API keys required.
- 📐 **Deterministic Logic:** Rigorous mathematical and statistical checks (Tukey's IQR, Z-scores, 2-sample Kolmogorov-Smirnov test, Population Stability Index).
- ⚖️ **Transparent Scoring:** Documented multi-dimensional scoring (Completeness, Validity, Uniqueness, Consistency) with an audit trail explaining every deduction.
- 📊 **Executive & Deep-Dive UI:** Built with dark navy SaaS aesthetics, responsive Plotly charts, and paginated exploration.
- 📦 **Multi-Format Exports:** Export full audit packages in machine-readable JSON, issues CSV, deduplicated dataset CSV, or self-contained standalone HTML.

---

## 🚀 Quick Start

### 1. Prerequisites 
- Python 3.10 or newer
- `pip` or virtualenv

### 2. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/DataSentinel-ai/datasentinel.git
cd datasentinel

# Create and activate virtual environment
# Windows (PowerShell):
python -m venv .venv 
.venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

### 3. Launch the Application

```bash
streamlit run datasentinel/app.py
```

Open your browser at **http://localhost:8501** to view DataSentinel.

---

## 🖥️ Application Features & Walkthrough

| Module | Description |
| :--- | :--- |
| **Overview Dashboard** | Executive summary, DataSentinel Quality Score gauge, KPI metric cards, severity breakdown, and sample preview. |
| **Dataset Explorer** | Interactive paginated record table with column filters, search query, sorting, and schema summary. |
| **Quality Analysis** | Deep-dive across 5 tabs: Missing Values, Duplicates, Type & Consistency, Numeric Outliers, and Custom Validation Rules. |
| **Column Profiler** | Statistical metrics for individual columns: Mean, Median, Std, Quantiles, Distribution Histograms, Boxplots, Categorical Frequencies, and Datetime timelines. |
| **Data Drift** | Baseline vs Current dataset comparison via 2-sample Kolmogorov-Smirnov test and Population Stability Index (PSI). |
| **Reports & Exports** | Generate and download machine-readable JSON, issue CSVs, deduplicated CSVs, and self-contained HTML audit reports. |
| **Settings & About** | Custom score weight calibration, outlier sensitivity adjustment, system environment telemetry, and offline guarantees. |

---

## 🏗️ Architecture

```
datasentinel/
├── app.py                      # Main Streamlit application entry point
├── components/                 # Reusable UI & visualization components
│   ├── charts.py               # Plotly charts with custom dark navy palette
│   ├── issue_tables.py         # Filterable findings tables & deduction lists
│   ├── metric_cards.py         # SaaS metric cards & custom CSS injection
│   └── sidebar.py              # Navigation, uploader, & dataset status
├── core/                       # Core configuration & runtime state
│   ├── config.py               # Global constants, thresholds, & color palette
│   ├── exceptions.py           # Domain exceptions
│   └── state.py                # Ephemeral Streamlit session state coordinator
├── engine/                     # Deterministic, testable analytical engines
│   ├── drift.py                # KS-test & PSI distribution shift detection
│   ├── duplicates.py           # Exact & subset duplicate analysis
│   ├── ingestion.py            # Robust CSV/Parquet parser & safety scanner
│   ├── missing_values.py       # Cell & pseudo-null string missingness analysis
│   ├── outliers.py             # Tukey IQR & Z-score outlier detectors
│   ├── profiling.py            # Numeric, categorical, & datetime statistical profiler
│   ├── report_builder.py       # JSON, CSV, and standalone HTML report generator
│   ├── scoring.py              # Transparent multi-dimensional scoring engine
│   ├── type_checks.py          # Numeric-in-text, mixed types, & zero-variance checks
│   └── validation.py           # Custom business constraint rule evaluator
├── pages/                      # Application route controllers
│   ├── column_profiler.py
│   ├── drift.py
│   ├── explorer.py
│   ├── overview.py
│   ├── quality_analysis.py
│   ├── reports.py
│   └── settings.py
├── schemas/                    # Typed dataclass schemas
│   ├── findings.py             # Findings, severity levels, & metadata schemas
│   └── rules.py                # Validation rule definitions & evaluation results
└── utils/                      # Formatting & file safety helpers
    ├── file_safety.py          # Header signature checks & size validation
    └── formatting.py           # Metric, byte, and badge formatters
```

---

## 🧪 Automated Testing & Quality Checks

Run the complete test suite with coverage:

```bash
pytest -v --cov=datasentinel --cov-report=term-missing tests/
```

Run code formatting and linting checks using Ruff:

```bash
# Check code style and lint rules
ruff check .

# Check formatting
ruff format --check .

# Auto-format codebase
ruff format .
```

---

## 🛡️ Security & Privacy

DataSentinel is built with a zero-trust model for local execution:
- **Passive Tabular Processing:** Data files are parsed strictly as passive structured records; macro scripts or formulas are never executed.
- **Header Signature Checks:** Automatically blocks executable files masquerading as CSVs (e.g. Windows PE, Linux ELF).
- **Stateless Operation:** Datasets are retained solely in volatile RAM during the Streamlit browser session and wiped upon reset.
- **Zero Cloud Exposure:** No private data leaves your local machine.

Read more in [docs/security.md](docs/security.md).

---

## 🗺️ Documentation

- 📐 [Architecture & Design Details](docs/architecture.md)
- ⚖️ [Quality Scoring Methodology & Formulas](docs/scoring.md)
- 🔒 [Security & Threat Model](docs/security.md)
- 🚀 [Project Roadmap](docs/roadmap.md)

---

## 🤝 Contributing

We welcome community contributions! Please review our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before opening pull requests.

## 📄 License

DataSentinel is open-source software licensed under the [MIT License](LICENSE).
