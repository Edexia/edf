# EDF Repository Constitution

**Guidelines for All Contributors (Humans & AI)**

---

## Mandatory Workflow

**Every change MUST follow this workflow. No exceptions.**

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. READ         Understand relevant code before writing            │
│         ↓                                                           │
│  2. IMPLEMENT    Make changes, write tests for 100% coverage        │
│         ↓                                                           │
│  3. TEST         Run `uv run pytest` - must pass with 100% coverage │
│         ↓                                                           │
│  4. DOCS         Spawn agents to check/update documentation         │
│         ↓                                                           │
│  5. SEMVER       Determine version bump (major/minor/patch)         │
│         ↓                                                           │
│  6. VERIFY       Final checks - tests, coverage, docs               │
│         ↓                                                           │
│  7. COMMIT       Commit atomically, immediately                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 1: READ

- Read all relevant files before making changes
- Understand existing patterns and conventions
- Check how similar features are implemented

### Step 2: IMPLEMENT

- Make minimal, focused changes
- Write tests for every new code path
- Follow existing code style and patterns
- Type hints on all public functions
- Docstrings on all public classes/methods

### Step 3: TEST

```bash
uv run pytest
```

**Requirements:**
- All tests must pass
- 100% code coverage (enforced by CI)
- No skipped tests without justification

### Step 4: DOCS

Spawn parallel agents to check if documentation needs updates:

| File | Update when... |
|------|----------------|
| `DOCS/CLI.md` | CLI commands, options, or behavior change |
| `DOCS/SDK.md` | Public API, classes, methods, or parameters change |
| `DOCS/SPEC.md` | File format, validation rules, or data structures change |

If any doc is outdated, update it before proceeding.

### Step 5: SEMVER

Determine the appropriate version bump:

| Change Type | Bump | Examples |
|-------------|------|----------|
| Breaking API changes | MAJOR | Removing public method, changing return types |
| New backward-compatible features | MINOR | Adding new class, new optional parameter |
| Bug fixes | PATCH | Fixing validation logic, correcting behavior |

**Update both files together:**
- `pyproject.toml`: `version = "X.Y.Z"`
- `src/edf/__init__.py`: `__version__ = "X.Y.Z"`

**Public API** (items in `__all__`) determines breaking changes:
- `EDF`, `Submission`, `EDF_VERSION`
- Exception classes: `EDFError`, `EDFValidationError`, `EDFStructureError`, `EDFConsistencyError`
- Model classes: `Manifest`, `TaskCore`, `GradeDistributions`, `SubmissionCore`, `SubmissionIndex`, `ContentFormat`, `AdditionalDataDeclaration`

### Step 6: VERIFY

Final checklist before commit:

```bash
uv run pytest                    # Tests pass, 100% coverage
git diff                         # Review all changes
```

- [ ] Tests pass with 100% coverage
- [ ] Documentation updated (if applicable)
- [ ] Version bumped (if applicable)
- [ ] No unrelated changes included

### Step 7: COMMIT

**Commit immediately and atomically.** Do not wait or batch changes.

```bash
git add -A
git commit -m "type: short description"
```

Commit message types:
- `feat`: New feature
- `fix`: Bug fix
- `test`: Test changes
- `docs`: Documentation
- `refactor`: Code refactoring
- `chore`: Maintenance (including version bumps)

For version bumps:
```bash
git commit -m "chore: bump version to X.Y.Z"
git tag vX.Y.Z
```

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
git clone https://github.com/Edexia/edf
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

## Project Structure

### Source Code

```
src/edf/
├── __init__.py      # Public API exports
├── core.py          # EDF and Submission classes
├── models.py        # Pydantic models
├── validation.py    # Validation logic
├── cli.py           # CLI implementation
└── exceptions.py    # Exception hierarchy
```

### Tests

```
tests/
├── conftest.py          # Shared fixtures
├── test_core.py         # Tests src/edf/core.py
├── test_models.py       # Tests src/edf/models.py
├── test_validation.py   # Tests src/edf/validation.py
├── test_cli.py          # Tests src/edf/cli.py
├── test_server.py       # Tests viewer/server.py
└── test_exceptions.py   # Tests src/edf/exceptions.py
```

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | Installation and quick start |
| `DOCS/CLI.md` | Command line interface reference |
| `DOCS/SDK.md` | Complete SDK reference |
| `DOCS/SPEC.md` | EDF file format specification |
| `CONSTITUTION.md` | This document |

---

## Testing Standards

### Naming Convention

```
test_{function}_{scenario}
```

### Requirements

- Use fixtures from `conftest.py`
- Tests must be independent and stateless
- Test all branches and edge cases

### Coverage Exclusions

Only these patterns may be excluded (defined in `pyproject.toml`):
- `pragma: no cover` (use sparingly, with justification)
- `if __name__ == "__main__":`
- `raise NotImplementedError`

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

*"Read. Implement. Test. Document. Version. Verify. Commit."*
