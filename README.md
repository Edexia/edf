# EDF - Edexia Data Format

A Python SDK and CLI for working with EDF files. An EDF file is a ZIP archive containing grading data for automated learning systems.

## Documentation

> **For Agents**: This repo's docs are designed for easy fetching via raw.githubusercontent.com.
> Construct URLs as: `https://raw.githubusercontent.com/Edexia/edf/main/{path}`

| Document | Description |
|----------|-------------|
| [DOCS/OVERVIEW.md](DOCS/OVERVIEW.md) | Concepts, purpose, architecture |
| [DOCS/COOKBOOK.md](DOCS/COOKBOOK.md) | Quick recipes for common tasks |
| [DOCS/CLI/README.md](DOCS/CLI/README.md) | CLI tool reference |
| [DOCS/SDK/README.md](DOCS/SDK/README.md) | Python SDK reference |
| [DOCS/SPEC/README.md](DOCS/SPEC/README.md) | File format specification |

### CLI Commands

| Command | Details |
|---------|---------|
| `edf info` | [DOCS/CLI/info.md](DOCS/CLI/info.md) |
| `edf validate` | [DOCS/CLI/validate.md](DOCS/CLI/validate.md) |
| `edf view` | [DOCS/CLI/view.md](DOCS/CLI/view.md) |

### SDK Classes

| Class | Details |
|-------|---------|
| `EDF` | [DOCS/SDK/EDF.md](DOCS/SDK/EDF.md) |
| `Submission` | [DOCS/SDK/Submission.md](DOCS/SDK/Submission.md) |
| `GradeDistributions` | [DOCS/SDK/GradeDistributions.md](DOCS/SDK/GradeDistributions.md) |
| `ContentFormat` | [DOCS/SDK/ContentFormat.md](DOCS/SDK/ContentFormat.md) |
| Exceptions | [DOCS/SDK/exceptions.md](DOCS/SDK/exceptions.md) |

### Specification

| Topic | Details |
|-------|---------|
| manifest.json | [DOCS/SPEC/manifest.md](DOCS/SPEC/manifest.md) |
| Task files | [DOCS/SPEC/task.md](DOCS/SPEC/task.md) |
| Submissions | [DOCS/SPEC/submissions.md](DOCS/SPEC/submissions.md) |
| Content hash | [DOCS/SPEC/content-hash.md](DOCS/SPEC/content-hash.md) |
| Additional data | [DOCS/SPEC/additional-data.md](DOCS/SPEC/additional-data.md) |
| Validation | [DOCS/SPEC/validation.md](DOCS/SPEC/validation.md) |

---

## Installation

### CLI tool

```bash
uv tool install git+https://github.com/Edexia/edf
```

### As a library

```bash
uv add git+https://github.com/Edexia/edf
```

### For development

```bash
git clone https://github.com/Edexia/edf
cd edf
uv sync
```

---

## Quick Start

### CLI

```bash
edf info assignment.edf
edf validate assignment.edf
edf view assignment.edf
```

### Python

```python
from edf import EDF

# Create
edf = EDF(max_grade=20)
edf.rubric = "# Criteria\n- Correctness: 10pts"
edf.add_submission(
    submission_id="alice",
    grade=15,
    optimistic=[0]*13 + [0.05, 0.15, 0.5, 0.2, 0.1, 0, 0, 0],
    expected=[0]*13 + [0.1, 0.2, 0.4, 0.2, 0.1, 0, 0, 0],
    pessimistic=[0]*12 + [0.1, 0.2, 0.3, 0.25, 0.1, 0.05, 0, 0, 0],
    content="Student answer...",
)
edf.save("output.edf")

# Read
with EDF.open("output.edf") as edf:
    for sub in edf.submissions:
        print(f"{sub.id}: {sub.grade}")
```

---

## File Format

EDF files are ZIP archives:

```
task.edf
├── manifest.json
├── task/
│   ├── core.json
│   ├── rubric.md (optional)
│   └── prompt.md (optional)
└── submissions/
    ├── _index.json
    └── {submission_id}/
        ├── core.json
        └── content.md | content.pdf | pages/
```

See [DOCS/SPEC/README.md](DOCS/SPEC/README.md) for full specification.

---

## License

MIT
