# EDF Python SDK

This document covers the Python SDK for reading and writing EDF files. For the command line interface, see [CLI.md](CLI.md). For the file format specification, see [SPEC.md](SPEC.md).

## Cookbook

Quick recipes for common tasks.

### Create a new EDF file

```python
from edf import EDF

edf = EDF(max_grade=20)
edf.rubric = "# Grading Criteria\n\n- Correctness: 10 points\n- Style: 10 points"
edf.prompt = "Write a function that reverses a string."

edf.add_submission(
    submission_id="student_alice",
    grade=18,
    optimistic=[0]*16 + [0.1, 0.2, 0.4, 0.2, 0.1],
    expected=[0]*15 + [0.1, 0.2, 0.4, 0.2, 0.1],
    pessimistic=[0]*14 + [0.1, 0.2, 0.3, 0.2, 0.1, 0.1],
    content="def reverse(s): return s[::-1]",
    student_name="Alice Smith",
)

edf.save("assignment.edf")
```

### Open and read an EDF file

```python
from edf import EDF

with EDF.open("assignment.edf") as edf:
    print(f"Task: {edf.task_id}")
    print(f"Max grade: {edf.max_grade}")
    print(f"Rubric: {edf.rubric}")

    for sub in edf.submissions:
        print(f"{sub.id}: {sub.grade}/{edf.max_grade}")
```

### Access submission content

```python
with EDF.open("assignment.edf") as edf:
    sub = edf.get_submission("student_alice")

    # Markdown content
    if text := sub.get_markdown():
        print(text)

    # PDF content
    if pdf_bytes := sub.get_pdf():
        with open("output.pdf", "wb") as f:
            f.write(pdf_bytes)

    # Image pages
    if images := sub.get_images():
        for i, img_bytes in enumerate(images):
            with open(f"page_{i}.jpg", "wb") as f:
                f.write(img_bytes)
```

### Add LLM grading context (important!)

The `llm_context` attribute provides per-submission information that an LLM grader needs for accurate assessment. **This is essential when context varies between submissions.**

```python
edf = EDF(max_grade=20)

# Submission where the student answered a specific question
edf.add_submission(
    submission_id="student_alice",
    grade=15,
    optimistic=[...], expected=[...], pessimistic=[...],
    content="The mitochondria is the powerhouse of the cell because...",
    llm_context="""
Question attempted: Q3 - Explain the role of mitochondria in cellular respiration.
Worth 20 marks. Award marks for: identifying ATP production (5), explaining
electron transport chain (10), mentioning oxygen's role (5).
""",
)

# Submission with OCR/handwriting notes
edf.add_submission(
    submission_id="student_bob",
    grade=12,
    optimistic=[...], expected=[...], pessimistic=[...],
    content="[OCR transcription of handwritten work]...",
    llm_context="""
Question attempted: Q3 - Explain the role of mitochondria.
OCR confidence: 87%. Page 2 paragraph 3 may have transcription errors.
Student has dyslexia accommodation - do not penalize spelling errors.
""",
)
```

Use `llm_context` for:
- The specific question/prompt the student answered
- OCR confidence warnings for scanned submissions
- Accommodation notes (dyslexia, ESL, extra time, etc.)
- Any per-student grading variations

### Add metadata to tasks and submissions

```python
edf = EDF(max_grade=100)

# Task-level metadata
edf.set_task_data(
    school_id="SCHOOL-001",
    subject_code="CS-101",
    academic_year="2025",
)

# Submission-level metadata (via **kwargs)
edf.add_submission(
    submission_id="student_bob",
    grade=85,
    optimistic=[...],
    expected=[...],
    pessimistic=[...],
    content="...",
    student_name="Bob Jones",      # additional
    student_id="2025-042",         # additional
    grader_id="prof_smith",        # additional
    llm_context="Question: Q5. No accommodations.",  # LLM context
)
```

### Validate an EDF file

```python
from edf import EDF, EDFValidationError

try:
    with EDF.open("file.edf", validate=True) as edf:
        print("Valid!")
except EDFValidationError as e:
    print("Invalid:")
    for error in e.errors:
        print(f"  - {error}")
```

### Copy and modify an EDF

```python
with EDF.open("original.edf") as edf:
    # Add a new submission
    edf.add_submission(
        submission_id="late_student",
        grade=14,
        optimistic=[...],
        expected=[...],
        pessimistic=[...],
        content="Late submission content...",
    )

    # Save as new file
    edf.save("updated.edf")
```

### Work with PDF submissions

```python
edf = EDF(max_grade=50)

with open("student_work.pdf", "rb") as f:
    pdf_bytes = f.read()

edf.add_submission(
    submission_id="student_1",
    grade=42,
    optimistic=[...],
    expected=[...],
    pessimistic=[...],
    content=pdf_bytes,  # bytes = PDF format
)

edf.save("pdf_submissions.edf")
```

### Work with image submissions

```python
edf = EDF(max_grade=10)

# Load scanned pages
pages = []
for i in range(3):
    with open(f"scan_page_{i}.jpg", "rb") as f:
        pages.append(f.read())

edf.add_submission(
    submission_id="handwritten_exam",
    grade=8,
    optimistic=[...],
    expected=[...],
    pessimistic=[...],
    content=pages,  # list[bytes] = images format
)

edf.save("scanned_exams.edf")
```

### Generate grade distributions

The three variance modes model **noise levels in human marker behavior**, not systematic biases:

- **optimistic**: Low noise — markers grade consistently. Use a tighter distribution.
- **expected**: Medium noise — typical marker variability.
- **pessimistic**: High noise — markers are inconsistent. Use a wider distribution.

**Important:** Avoid using naive standard deviations (e.g., `std=1.5` for all submissions). Real marker noise varies based on factors like rubric clarity, question ambiguity, and submission quality. Consider modeling these factors rather than using fixed spreads.

If you need a simple helper for prototyping, use spread-based generation:

```python
import math

def generate_distribution(peak: int, max_grade: int, spread: float = 0.15) -> list[float]:
    """
    Generate a bell-curve distribution centered on peak.

    The spread parameter controls distribution width as a fraction of max_grade.
    Lower spread = tighter distribution (low noise), higher spread = wider (high noise).

    Note: For production use, consider deriving spread from actual marker behavior
    data rather than using fixed values.
    """
    dist = []
    for i in range(max_grade + 1):
        diff = abs(i - peak)
        prob = math.exp(-(diff ** 2) / (2 * (spread * max_grade) ** 2))
        dist.append(prob)
    total = sum(dist)
    return [p / total for p in dist]

# Example for a grade of 15/20
optimistic = generate_distribution(15, 20, spread=0.10)   # Low noise (tight)
expected = generate_distribution(15, 20, spread=0.15)     # Medium noise
pessimistic = generate_distribution(15, 20, spread=0.20)  # High noise (wide)
```

---

## Full Reference

Complete API documentation.

### EDF

The main class for creating and reading EDF files.

#### Constructor

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
| `task_id` | `str \| None` | `None` | UUID v4. Auto-generated if not provided |
| `version` | `int` | `1` | Task version number |
| `edf_version` | `str` | `"1.0.0"` | EDF format version |

#### Class Methods

##### EDF.open

```python
EDF.open(path: str | Path, validate: bool = True) -> EDF
```

Open an existing EDF file.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str \| Path` | required | Path to .edf file |
| `validate` | `bool` | `True` | Validate file on open |

Raises `EDFValidationError` if validation fails.

#### Properties

| Property | Type | Writable | Description |
|----------|------|----------|-------------|
| `task_id` | `str` | No | UUID v4 identifier |
| `version` | `int` | Yes | Task version (≥ 1) |
| `edf_version` | `str` | No | Format version |
| `max_grade` | `int` | No | Maximum grade |
| `rubric` | `str \| None` | Yes | Rubric markdown |
| `prompt` | `str \| None` | Yes | Prompt markdown |
| `task_data` | `dict[str, Any]` | No | Task metadata (use `set_task_data` to modify) |
| `created_at` | `int \| None` | No | Unix ms timestamp (after save) |
| `content_hash` | `str \| None` | No | SHA256 hash (after save) |
| `submissions` | `list[Submission]` | No | All submissions |
| `submission_ids` | `list[str]` | No | All submission IDs |
| `content_format` | `ContentFormat \| None` | No | Format of submissions |

#### Methods

##### set_task_data

```python
edf.set_task_data(**kwargs: Any) -> EDF
```

Set task-level metadata. Returns `self` for chaining.

##### get_submission

```python
edf.get_submission(submission_id: str) -> Submission
```

Get submission by ID. Raises `KeyError` if not found.

##### add_submission

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
| `grade` | `int` | Ground truth grade in [0, max_grade] |
| `optimistic` | `list[float]` | Optimistic distribution (length = max_grade + 1) |
| `expected` | `list[float]` | Expected distribution |
| `pessimistic` | `list[float]` | Pessimistic distribution |
| `content` | `str \| bytes \| list[bytes]` | Content (see below) |
| `**additional` | `Any` | Submission metadata |

Content format is inferred from type:
- `str` → markdown
- `bytes` → PDF
- `list[bytes]` → images (JPEGs)

All submissions must use the same format.

##### remove_submission

```python
edf.remove_submission(submission_id: str) -> EDF
```

Remove submission by ID. Raises `KeyError` if not found.

##### save

```python
edf.save(path: str | Path) -> None
```

Save to file. Raises `ValueError` if no submissions or invalid data.

##### close

```python
edf.close() -> None
```

Close underlying ZIP file. Called automatically when using `with` statement.

#### Context Manager

```python
with EDF.open("file.edf") as edf:
    # edf.close() called automatically
    pass
```

---

### Submission

A submission within an EDF file.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Submission identifier |
| `grade` | `int` | Ground truth grade |
| `distributions` | `GradeDistributions` | The three distributions |
| `content` | `str \| bytes \| list[bytes]` | Raw content |
| `additional` | `dict[str, Any]` | Submission metadata |
| `content_format` | `ContentFormat` | Detected format |

#### Methods

##### get_markdown

```python
submission.get_markdown() -> str | None
```

Returns markdown content, or `None` if not markdown format.

##### get_pdf

```python
submission.get_pdf() -> bytes | None
```

Returns PDF bytes, or `None` if not PDF format.

##### get_images

```python
submission.get_images() -> list[bytes] | None
```

Returns list of JPEG bytes, or `None` if not images format.

---

### GradeDistributions

Container for the three probability distributions representing different marker noise levels.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `optimistic` | `list[float]` | Low-noise scenario (tight distribution) |
| `expected` | `list[float]` | Medium-noise scenario (baseline) |
| `pessimistic` | `list[float]` | High-noise scenario (wide distribution) |

Each distribution:
- Has length `max_grade + 1`
- Contains non-negative values
- Sums to 1.0 (within 0.0001 tolerance)

Note: These modes model noise/variance in marker behavior, not systematic biases.

---

### ContentFormat

Enum for content formats.

```python
from edf import ContentFormat

ContentFormat.MARKDOWN  # "markdown"
ContentFormat.PDF       # "pdf"
ContentFormat.IMAGES    # "images"
```

---

### Exceptions

#### EDFError

Base exception for all EDF errors.

#### EDFValidationError

Validation failure. Has `errors: list[str]` attribute with specific messages.

```python
try:
    with EDF.open("bad.edf") as edf:
        pass
except EDFValidationError as e:
    for msg in e.errors:
        print(msg)
```

#### EDFStructureError

Missing required files in archive.

#### EDFConsistencyError

Cross-file data mismatches (e.g., task_id doesn't match).

---

### Constants

```python
from edf import EDF_VERSION

print(EDF_VERSION)  # "1.0.0"
```
