# EDF Class

> **Navigation**: [SDK](README.md) | [Submission](Submission.md) | [GradeDistributions](GradeDistributions.md)

The main class for creating and reading EDF files.

## Constructor

```python
EDF(
    max_grade: int,
    task_id: str | None = None,
    version: int = 1,
    edf_version: str = "1.0.0",
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_grade` | `int` | required | Maximum possible grade |
| `task_id` | `str \| None` | `None` | UUID v4. Auto-generated if None |
| `version` | `int` | `1` | Task version number |
| `edf_version` | `str` | `"1.0.0"` | EDF format version |

## Class Methods

### EDF.open

```python
EDF.open(path: str | Path, validate: bool = True) -> EDF
```

Open an existing EDF file.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str \| Path` | required | Path to .edf file |
| `validate` | `bool` | `True` | Validate on open |

Raises `EDFValidationError` if validation fails.

### EDF.from_directory

```python
EDF.from_directory(
    path: str | Path,
    dangerously_load_unzipped_edf: bool = False,
) -> EDF
```

Load from unzipped directory. See [ephemeral.md](ephemeral.md).

## Properties

| Property | Type | Writable | Description |
|----------|------|----------|-------------|
| `task_id` | `str` | No | UUID v4 identifier |
| `version` | `int` | Yes | Task version (>= 1) |
| `edf_version` | `str` | No | Format version |
| `max_grade` | `int` | No | Maximum grade |
| `rubric` | `str \| None` | Yes | Rubric markdown |
| `prompt` | `str \| None` | Yes | Prompt markdown |
| `task_data` | `dict[str, Any]` | No | Task metadata |
| `created_at` | `int \| None` | No | Unix ms timestamp |
| `content_hash` | `str \| None` | No | SHA256 hash |
| `submissions` | `list[Submission]` | No | All submissions |
| `submission_ids` | `list[str]` | No | All submission IDs |
| `content_format` | `ContentFormat \| None` | No | Format of content |
| `is_ephemeral` | `bool` | No | True if from directory |

## Instance Methods

### set_task_data

```python
edf.set_task_data(**kwargs: Any) -> EDF
```

Set task-level metadata. Returns `self` for chaining.

```python
edf.set_task_data(
    school_id="SCHOOL-001",
    subject_code="CS-101",
)
```

### get_submission

```python
edf.get_submission(submission_id: str) -> Submission
```

Get submission by ID. Raises `KeyError` if not found.

### add_submission

```python
edf.add_submission(
    submission_id: str,
    grade: int,
    optimistic: list[float],
    expected: list[float],
    pessimistic: list[float],
    content: str | bytes | list[bytes],
    **additional: Any,
) -> EDF
```

Add a submission. Returns `self` for chaining.

| Parameter | Type | Description |
|-----------|------|-------------|
| `submission_id` | `str` | Unique ID (alphanumeric + underscores) |
| `grade` | `int` | Ground truth grade [0, max_grade] |
| `optimistic` | `list[float]` | Low-noise distribution |
| `expected` | `list[float]` | Baseline distribution |
| `pessimistic` | `list[float]` | High-noise distribution |
| `content` | `str \| bytes \| list[bytes]` | Content (see below) |
| `**additional` | `Any` | Metadata (student_name, llm_context, etc.) |

**Content format inference:**
- `str` -> markdown
- `bytes` -> PDF
- `list[bytes]` -> images (JPEGs)

All submissions must use the same format.

### remove_submission

```python
edf.remove_submission(submission_id: str) -> EDF
```

Remove by ID. Raises `KeyError` if not found.

### save

```python
edf.save(path: str | Path) -> None
```

Save to file. Raises `ValueError` if no submissions.

### close

```python
edf.close() -> None
```

Close underlying ZIP. Called automatically with `with`.

## Context Manager

```python
with EDF.open("file.edf") as edf:
    # edf.close() called automatically
    pass
```
