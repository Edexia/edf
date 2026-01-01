# EDF - Edexia Data Format

A Python SDK and tools for working with EDF files. An EDF file is a ZIP archive containing grading data for automated learning systems: one file per task, with a rubric, prompt, and any number of student submissions.

## Installation

### CLI tool (recommended)

Install the `edf` command globally:

```bash
uv tool install git+https://github.com/10decikelvin/edf
```

Then use it directly:

```bash
edf view assignment.edf
edf validate assignment.edf
edf info assignment.edf
```

### As a library

Add to your project:

```bash
uv add git+https://github.com/10decikelvin/edf
```

### For development

```bash
git clone https://github.com/10decikelvin/edf
cd edf
uv sync
```

## Quick Start

### Reading an EDF File

```python
from edf import EDF

with EDF.open("assignment.edf") as edf:
    print(f"Task: {edf.task_id}")
    print(f"Max grade: {edf.max_grade}")

    if edf.rubric:
        print(f"Rubric:\n{edf.rubric}")

    for sub in edf.submissions:
        print(f"{sub.id}: {sub.grade}")
        if text := sub.get_markdown():
            print(f"  Content: {text[:100]}...")
```

### Creating an EDF File

```python
from edf import EDF

edf = EDF(max_grade=20)
edf.rubric = """
# Grading Criteria

- Correctness: 10 points
- Clarity: 5 points
- Style: 5 points
"""

edf.add_submission(
    submission_id="student_alice",
    grade=15,
    optimistic=[0]*13 + [0.05, 0.15, 0.5, 0.2, 0.1, 0, 0, 0],
    expected=[0]*13 + [0.1, 0.2, 0.4, 0.2, 0.1, 0, 0, 0],
    pessimistic=[0]*12 + [0.1, 0.2, 0.3, 0.25, 0.1, 0.05, 0, 0, 0],
    content="The student's markdown answer here...",
    student_name="Alice Smith",
)

edf.save("output.edf")
```

### Validation

```python
from edf import EDF, EDFValidationError

try:
    with EDF.open("file.edf", validate=True) as edf:
        print("File is valid")
except EDFValidationError as e:
    print("Validation failed:")
    for error in e.errors:
        print(f"  - {error}")
```

## CLI Commands

After installing with `uv tool install`:

```bash
edf info assignment.edf       # Show file information
edf validate assignment.edf   # Validate a file
edf view assignment.edf       # Open the web viewer
edf view assignment.edf -p 9000  # Custom port
```

Or run without installing using `uvx`:

```bash
uvx --from git+https://github.com/10decikelvin/edf edf view assignment.edf
```

## Web Viewer

The web viewer provides a browser-based interface for exploring EDF files. It runs a local server that serves the file with range request support, allowing the browser to efficiently read large archives.

```bash
edf view large_dataset.edf
```

The viewer displays:
- Task information (ID, version, max grade, content format)
- Rubric and prompt (if present)
- List of all submissions
- Per-submission grade and grade distribution charts
- Submission content (markdown, PDF, or images)

## Documentation

- **[DOCS/SDK.md](DOCS/SDK.md)** — Exhaustive Python SDK reference (classes, methods, examples)
- **[DOCS/SPEC.md](DOCS/SPEC.md)** — EDF file format specification (schemas, validation rules, algorithms)

## File Format

EDF files are ZIP archives with a specific structure:

```
task.edf
├── manifest.json
├── task/
│   ├── core.json
│   ├── additional_data.json (optional)
│   ├── rubric.md (optional)
│   └── prompt.md (optional)
└── submissions/
    ├── _index.json
    └── {submission_id}/
        ├── core.json
        ├── additional_data.json (optional)
        └── content.md | content.pdf | pages/
```

## License

MIT
