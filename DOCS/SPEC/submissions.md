# Submissions

> **Navigation**: [Spec](README.md) | [manifest](manifest.md) | [task](task.md)

Files in the `submissions/` directory.

## submissions/_index.json

Required. Lists all submission IDs.

```json
{
  "submission_ids": ["student_a_2024", "student_b_2024", "student_c_2024"]
}
```

Length must equal `submission_count` in manifest.

## submissions/{id}/core.json

Required for each submission. Contains grade and distributions.

```json
{
  "submission_id": "student_a_2024",
  "grade": 15,
  "grade_distributions": {
    "optimistic": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.05, 0.15, 0.5, 0.2, 0.1, 0, 0, 0],
    "expected": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.4, 0.2, 0.1, 0, 0, 0],
    "pessimistic": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.3, 0.25, 0.1, 0.05, 0, 0, 0]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `submission_id` | string | Must match folder name |
| `grade` | number | Integer in [0, max_grade] |
| `grade_distributions` | object | Three probability arrays |

### submission_id Format

Alphanumeric characters and underscores only: `[a-zA-Z0-9_]+`

## Grade Distributions

Each distribution is an array of probabilities where index `i` = probability of grade `i`.

| Distribution | Noise Level | Shape |
|--------------|-------------|-------|
| `optimistic` | Low | Tight (small variance) |
| `expected` | Medium | Baseline |
| `pessimistic` | High | Wide (large variance) |

**Requirements:**
- Length = `max_grade + 1`
- All values >= 0
- Sum = 1.0 (within 0.0001 tolerance)

**Note:** These model marker noise/variance, not bias (harsh vs lenient).

## submissions/{id}/additional_data.json

Required if `additional_data.submission` in manifest is non-empty.

```json
{
  "student_name": "Alice Smith",
  "grader_id": "teacher_jane",
  "llm_context": "Question: Q3 - Explain photosynthesis."
}
```

## Content Files

Each submission has exactly ONE of:

| Format | File(s) | Description |
|--------|---------|-------------|
| markdown | `content.md` | Plain text/markdown |
| pdf | `content.pdf` | PDF document |
| images | `pages/0.jpg`, `pages/1.jpg`, ... | Numbered JPEGs |

Must match `content_format` in manifest.

## Directory Structure

```
submissions/
├── _index.json              # Required
└── student_a_2024/
    ├── core.json            # Required
    ├── additional_data.json # If declared
    └── content.md           # Or content.pdf or pages/
```
