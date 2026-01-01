# EDF Repository Constitution

**Guidelines for All Contributors (Humans & AI)**

---

## The Prime Directive

**100% test coverage is mandatory.** Every line, every branch, every path. CI will enforce this.

---

## Development Environment

### Required: uv

This project uses [uv](https://docs.astral.sh/uv/) for Python package management.

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/10decikelvin/edf
cd edf
uv sync
```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_core.py

# View HTML coverage report
open htmlcov/index.html
```

### Running CLI

```bash
uv run edf info example.edf
uv run edf validate example.edf
uv run edf view example.edf
```

---

## Semantic Versioning

This project follows [SemVer 2.0.0](https://semver.org/). Version format: `MAJOR.MINOR.PATCH`

| When to bump | Version | Examples |
|--------------|---------|----------|
| Breaking API changes | MAJOR | Removing public method, changing return types |
| New backward-compatible features | MINOR | Adding new class, new optional parameter |
| Bug fixes | PATCH | Fixing validation logic, correcting behavior |

### Version Locations

Both files MUST be updated together:
- `pyproject.toml`: `version = "X.Y.Z"`
- `src/edf/__init__.py`: `__version__ = "X.Y.Z"`

### Public API

The public API (items in `__all__`) determines what constitutes a breaking change:
- `EDF`, `Submission`, `EDF_VERSION`
- Exception classes: `EDFError`, `EDFValidationError`, `EDFStructureError`, `EDFConsistencyError`
- Model classes: `Manifest`, `TaskCore`, `GradeDistributions`, `SubmissionCore`, `SubmissionIndex`, `ContentFormat`, `AdditionalDataDeclaration`

---

## Testing Requirements

### When to Run Tests

- Before every commit
- After any code change
- Before opening a PR

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_core.py         # Tests src/edf/core.py
├── test_models.py       # Tests src/edf/models.py
├── test_validation.py   # Tests src/edf/validation.py
├── test_cli.py          # Tests src/edf/cli.py
├── test_exceptions.py   # Tests src/edf/exceptions.py
└── test_submission.py   # Additional submission tests
```

### Writing Tests

- Name tests: `test_{function}_{scenario}`
- Use fixtures from `conftest.py`
- Tests must be independent and stateless
- Test all branches and edge cases

### Coverage Exclusions

Only these patterns may be excluded (defined in `pyproject.toml`):
- `pragma: no cover` (use sparingly, with justification)
- `if __name__ == "__main__":`
- `raise NotImplementedError`

---

## Code Standards

### File Structure

```
src/edf/
├── __init__.py      # Public API exports
├── core.py          # EDF and Submission classes
├── models.py        # Pydantic models
├── validation.py    # Validation logic
├── cli.py           # CLI implementation
└── exceptions.py    # Exception hierarchy
```

### Requirements

- Type hints on all public functions and methods
- Docstrings on all public classes and methods
- Follow existing code patterns

---

## Git Practices

### Commit Messages

```
type: short description

# Types:
feat:     New feature
fix:      Bug fix
test:     Test changes
docs:     Documentation
refactor: Code refactoring
chore:    Maintenance
```

### Pre-Commit Checklist

```bash
uv run pytest           # All tests pass, 100% coverage
git diff main           # Review changes
```

### Version Bump Commits

```bash
# After updating version in both files:
git commit -m "chore: bump version to X.Y.Z"
git tag vX.Y.Z
```

---

## For AI Assistants

1. **Read before writing** - Understand existing code first
2. **Run tests** - Use `uv run pytest` to verify changes
3. **Match patterns** - Follow existing code style
4. **Minimal changes** - Only what's necessary
5. **Write tests** - Every new path needs coverage

---

## Documentation

| File | Purpose |
|------|---------|
| `README.md` | Installation and quick start |
| `DOCS/SDK.md` | Complete SDK reference |
| `DOCS/SPEC.md` | EDF file format specification |
| `CONSTITUTION.md` | This document |

Update documentation when changing public API.

---

## Dependencies

Managed via `pyproject.toml` and locked in `uv.lock`.

```bash
# Add a dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Sync environment
uv sync
```

Keep dependencies minimal. Currently:
- Runtime: `pydantic>=2.0`
- Dev: `pytest>=8.0`, `pytest-cov>=4.0`

---

*"Test first. Cover everything. Ship with confidence."*
