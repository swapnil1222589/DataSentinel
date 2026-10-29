# Contributing to DataSentinel

Thank you for your interest in contributing to **DataSentinel**! We welcome bug reports, feature suggestions, documentation enhancements, and code contributions.

---

## 🧭 Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to `maintainers@datasentinel.dev`.

---

## 🛠️ Development Setup

1. **Fork and Clone the Repository:**
   ```bash 
   git clone https://github.com/<your-username>/datasentinel.git
   cd datasentinel
   ```

2. **Create a Virtual Environment:**
   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install Development Dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Verify Installation:**
   ```bash
   pytest
   ruff check .
   ```

---

## 🔄 Development Workflow

1. Create a descriptive topic branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Write clean, modular Python code adhering to the repository architecture:
   - Analytical and statistical computations belong in `datasentinel/engine/`.
   - UI widgets and view controllers belong in `datasentinel/pages/` or `datasentinel/components/`.
   - All public functions should have descriptive docstrings and type annotations.
3. Write automated tests in `tests/` with deterministic assertions.
4. Run formatting and linting:
   ```bash
   ruff format .
   ruff check . --fix
   ```
5. Ensure all tests pass:
   ```bash
   pytest -v --cov=datasentinel tests/
   ```
6. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat(drift): add population stability index threshold configuration"
   ```
7. Push your branch and open a Pull Request.

---

## 📝 Pull Request Checklist

Before submitting your PR, ensure:
- [ ] New functionality is covered by automated unit tests in `tests/`.
- [ ] Tests pass locally across all test modules.
- [ ] `ruff check .` and `ruff format --check .` succeed without warnings.
- [ ] Documentation has been updated to reflect any new features or changed behavior.
- [ ] PR description clearly explains the problem solved and testing performed.
