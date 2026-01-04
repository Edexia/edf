# SDK Reference

> **Navigation**: [Home](../../README.md) | [Overview](../OVERVIEW.md) | [Cookbook](../COOKBOOK.md) | [CLI](../CLI/README.md) | [Spec](../SPEC/README.md)

Python SDK for reading and writing EDF files.

## Installation

```bash
# Add to project
uv add git+https://github.com/Edexia/edf

# Or with pip
pip install git+https://github.com/Edexia/edf
```

## Quick Example

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

## API Reference

| Class | Description | Details |
|-------|-------------|---------|
| `EDF` | Main class for reading/writing | [EDF.md](EDF.md) |
| `Submission` | A submission within an EDF | [Submission.md](Submission.md) |
| `GradeDistributions` | Three probability distributions | [GradeDistributions.md](GradeDistributions.md) |
| `ContentFormat` | Enum for content types | [ContentFormat.md](ContentFormat.md) |

## Exceptions

| Exception | Description | Details |
|-----------|-------------|---------|
| `EDFError` | Base exception | [exceptions.md](exceptions.md) |
| `EDFValidationError` | Validation failure | [exceptions.md](exceptions.md#edfvalidationerror) |
| `EDFStructureError` | Missing files | [exceptions.md](exceptions.md#edfstructureerror) |
| `EDFConsistencyError` | Data mismatch | [exceptions.md](exceptions.md#edfconsistencyerror) |

## Other Topics

| Topic | Description | Details |
|-------|-------------|---------|
| Ephemeral EDFs | Working with unzipped directories | [ephemeral.md](ephemeral.md) |

## Imports

```python
from edf import (
    # Main classes
    EDF,
    Submission,

    # Enums
    ContentFormat,

    # Exceptions
    EDFError,
    EDFValidationError,
    EDFStructureError,
    EDFConsistencyError,

    # Constants
    EDF_VERSION,
    EPHEMERAL_TASK_ID,
    EPHEMERAL_VERSION,
)
```
