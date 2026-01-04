# Exceptions

> **Navigation**: [SDK](README.md) | [EDF](EDF.md)

Exception hierarchy for EDF operations.

## Hierarchy

```
EDFError
├── EDFValidationError
├── EDFStructureError
└── EDFConsistencyError
```

## EDFError

Base exception for all EDF errors.

```python
from edf import EDFError

try:
    # Any EDF operation
    pass
except EDFError as e:
    print(f"EDF error: {e}")
```

## EDFValidationError

Validation failure. Has `errors: list[str]` attribute with specific messages.

```python
from edf import EDF, EDFValidationError

try:
    with EDF.open("bad.edf", validate=True) as edf:
        pass
except EDFValidationError as e:
    print("Validation failed:")
    for msg in e.errors:
        print(f"  - {msg}")
```

### Common Validation Errors

| Error | Cause |
|-------|-------|
| Distribution length wrong | Array length != max_grade + 1 |
| Distribution sum != 1.0 | Probabilities don't sum to 1 |
| Grade out of range | Grade < 0 or > max_grade |
| Undeclared attribute | Additional data not in manifest |
| Submission count mismatch | Manifest disagrees with _index.json |

## EDFStructureError

Missing required files in archive.

```python
from edf import EDF, EDFStructureError

try:
    with EDF.open("incomplete.edf") as edf:
        pass
except EDFStructureError as e:
    print(f"Missing files: {e}")
```

### Required Files

- `manifest.json`
- `task/core.json`
- `submissions/_index.json`
- `submissions/{id}/core.json` for each submission

## EDFConsistencyError

Cross-file data mismatches.

```python
from edf import EDF, EDFConsistencyError

try:
    with EDF.open("inconsistent.edf") as edf:
        pass
except EDFConsistencyError as e:
    print(f"Data mismatch: {e}")
```

### Common Consistency Errors

| Error | Cause |
|-------|-------|
| Task ID mismatch | manifest.json != task/core.json |
| Submission count mismatch | manifest != _index.json length |
| Folder name mismatch | Folder name != submission_id in core.json |

## Imports

```python
from edf import (
    EDFError,
    EDFValidationError,
    EDFStructureError,
    EDFConsistencyError,
)
```
