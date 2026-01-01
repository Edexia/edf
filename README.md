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
from edf import EDFReader

with EDFReader.open("assignment.edf") as reader:
    print(f"Task: {reader.manifest.task_id}")
    print(f"Max grade: {reader.task.core.max_grade}")

    if reader.rubric:
        print(f"Rubric:\n{reader.rubric}")

    for submission in reader.iter_submissions():
        print(f"{submission.submission_id}: {submission.grade}")

        # Access grade distributions
        dist = submission.grade_distributions
        print(f"  Expected distribution peak: {dist.expected.index(max(dist.expected))}")

        # Get content (format depends on manifest.content_format)
        if content := submission.get_content_markdown():
            print(f"  Content: {content[:100]}...")
```

### Creating an EDF File

```python
from edf import EDFBuilder

builder = EDFBuilder()
builder.set_max_grade(20)
builder.set_rubric("""
# Grading Criteria

- Correctness: 10 points
- Clarity: 5 points
- Style: 5 points
""")

# Add submissions with grade distributions
builder.add_submission(
    submission_id="student_alice",
    grade=15,
    optimistic=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.05, 0.15, 0.5, 0.2, 0.1, 0, 0, 0],
    expected=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.4, 0.2, 0.1, 0, 0, 0],
    pessimistic=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.3, 0.25, 0.1, 0.05, 0, 0, 0],
    content="The student's markdown answer here...",
    student_name="Alice Smith",  # additional data
)

builder.write("output.edf")
```

### Validation

```python
from edf import EDFReader
from edf.exceptions import EDFValidationError

try:
    with EDFReader.open("file.edf", validate=True) as reader:
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

## File Format

EDF files are ZIP archives with a specific structure. See [DOCS/SPEC.md](DOCS/SPEC.md) for the complete specification.

Basic structure:
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

## Additional Data

EDF supports additional metadata attributes at both the task and submission level. Standard attributes include:

**Task level:** `school_id`, `subject_code`, `time_limit_minutes`, `academic_year`, `difficulty_level`, `source_exam`, `section_id`

**Submission level:** `student_name`, `student_id`, `grader_id`, `submitted_at`, `graded_at`, `time_taken_minutes`, `attempt_number`, `marker_feedback`

Custom attributes can use the `x-{namespace}-{attribute}` pattern without requiring registration.

## License

MIT
