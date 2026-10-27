# Security Policy

The DataSentinel open-source team takes security and user privacy seriously.

## Supported Versions

Only the latest release of DataSentinel receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within DataSentinel:

1. **Do not disclose the vulnerability publicly.** Do not open a public GitHub issue.
2. Email your findings directly to `security@datasentinel.dev` with:
   - Type of vulnerability (e.g., path traversal, memory leak, unsafe deserialization).
   - Clear steps to reproduce the issue (including minimal synthetic data sample).
   - Potential impact and any proposed mitigations.
3. We will acknowledge receipt of your vulnerability report within 48 hours and provide an estimated timeline for a patch.

## Security Practices in DataSentinel

- **Offline by Default:** Datasets uploaded to DataSentinel never leave your workstation.
- **No Deserialization of Code:** Tabular datasets are strictly parsed into numeric and string memory structures.
- **Continuous Security Testing:** CI pipelines run security linters and automated tests on every pull request.
