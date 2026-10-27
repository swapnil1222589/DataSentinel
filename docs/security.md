# DataSentinel Security & Privacy Model

DataSentinel was built from the ground up as a **zero-trust, privacy-first, local-execution** platform.

## Core Security Tenets

1. **Local-Only Processing:** Datasets are processed directly in your local workstation memory. No data is ever transmitted to remote servers, analytics trackers, or external cloud endpoints.
2. **Never Execute Uploaded Content:** Uploaded files (CSV and Parquet) are parsed strictly as passive structured tabular data. Formulas, macro scripts, and binary executables are stripped or rejected.
3. **Protection Against Path Traversal:** Uploaded filenames are sanitized (`sanitize_filename`) to strip null bytes, relative directory paths (`../`), and prohibited filesystem characters.
4. **Header Signature Verification:** Uploaded files undergo magic-byte signature inspection to immediately reject disguised Windows PE executables (`MZ`), Linux binaries (`\x7fELF`), or Mach-O binaries.
5. **Memory & Upload Guardrails:** A configurable upload ceiling (default 100 MB) prevents memory exhaustion (DoS).
6. **Stateless Sessions:** Datasets exist only in Streamlit's ephemeral memory session state and are completely destroyed upon session restart or explicit reset. No SQLite or file-based persistence is enabled by default.

---

## Threat Model & Mitigations

| Threat Vector | Mitigation Strategy |
| :--- | :--- |
| **Malicious Executable Upload** | Magic byte validation (`validate_file_safety`) inspects initial buffer bytes before parsing. |
| **Formula Injection (CSV Injection)** | DataSentinel does not evaluate formula syntax (`=CMD`, `@`, `+`, `-`) as shell commands. Data is ingested purely into typed NumPy/Pandas arrays. |
| **Memory Exhaustion (Denial of Service)** | File size limits strictly enforced at both Streamlit server level (`config.toml`) and ingestion validation layer. |
| **Data Leakage via Telemetry** | Streamlit telemetry tracking is disabled (`gatherUsageStats = false`). Zero third-party trackers or CDNs are embedded. |
| **AI Data Exfiltration** | AI integrations are strictly optional, defaulted to `none`, and gated behind interfaces that forbid sending raw tabular rows. |
