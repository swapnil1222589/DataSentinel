# DataSentinel Project Roadmap

## Phase 1: MVP & Core Observability (Completed ✅)
- [x] Streamlit-based interactive developer dashboard with dark navy aesthetics.
- [x] Fast ingestion for CSV and Parquet files with multi-encoding recovery and duplicate column disambiguation.
- [x] Missing value analysis with pseudo-null detection and visual sparsity charts.
- [x] Duplicate record analysis (exact and subset-based) with non-destructive deduplication export.
- [x] Data type integrity checks (numeric stored as text, mixed types, constant columns, untrimmed whitespace).
- [x] Outlier detection via Tukey's IQR and Z-scores with interactive threshold adjustment.
- [x] Custom domain validation rules engine (Range, Non-negative, Not-null, Unique, Allowed values, Regex).
- [x] Transparent 4-dimension scoring engine with deduction breakdown and critical issue cap.
- [x] Column profiler with histograms, boxplots, categorical frequencies, and datetime timeline analysis.
- [x] Data Drift module using 2-sample Kolmogorov-Smirnov test and Population Stability Index (PSI).
- [x] Multi-format exports: Machine-readable JSON, Issues CSV, Cleaned Data CSV, Standalone HTML report.
- [x] Automated pytest test suite covering all modules.
- [x] CI/CD automation with GitHub Actions and Ruff linting.

## Phase 2: Enhanced Ingestion & Connectors (Upcoming 🚀)
- [ ] Direct SQL database connection connectors (PostgreSQL, SQLite, Snowflake read-only).
- [ ] Arrow IPC and Feather format ingestion.
- [ ] Chunked out-of-core streaming ingestion with Polars for multi-gigabyte datasets.

## Phase 3: Advanced ML Observability
- [ ] Target leakage detection and high correlation anomaly warnings.
- [ ] Multivariate drift detection using Maximum Mean Discrepancy (MMD).
- [ ] Concept drift and label shift monitoring.

## Phase 4: CI/CD Quality Gates & CLI
- [ ] Headless CLI runner (`datasentinel audit --file data.csv --fail-below 85`).
- [ ] Pre-commit hooks for data scientists committing sample datasets.
- [ ] Webhook notifications for Slack, Discord, and Teams.
