# Validation Rules

> **Navigation**: [Spec](README.md) | [manifest](manifest.md) | [submissions](submissions.md)

Complete validation requirements for EDF files.

## Structural Validation

### Required Files

These files must exist:
- `manifest.json`
- `task/core.json`
- `submissions/_index.json`

For each submission ID in `_index.json`:
- `submissions/{id}/core.json`

### Conditional Files

| Condition | Required File |
|-----------|---------------|
| `additional_data.task` non-empty | `task/additional_data.json` |
| `additional_data.submission` non-empty | `submissions/{id}/additional_data.json` for each |
| `has_rubric=true` | `task/rubric.md` |
| `has_prompt=true` | `task/prompt.md` |

### Content Files

Each submission needs exactly one of:
- `content.md` (if `content_format="markdown"`)
- `content.pdf` (if `content_format="pdf"`)
- `pages/` directory with `0.jpg`, `1.jpg`, ... (if `content_format="images"`)

## Consistency Validation

| Check | Rule |
|-------|------|
| Task ID | `manifest.task_id` == `task/core.json.task_id` |
| Submission count | `manifest.submission_count` == length of `_index.json.submission_ids` |
| Submission IDs | Each folder name == `core.json.submission_id` inside it |
| Content format | All submissions match `manifest.content_format` |

## Data Validation

### Grade Distributions

For each distribution (`optimistic`, `expected`, `pessimistic`):

| Check | Rule |
|-------|------|
| Length | Array length == `max_grade + 1` |
| Values | All values >= 0 |
| Sum | Sum == 1.0 (tolerance: 0.0001) |

### Grades

| Check | Rule |
|-------|------|
| Range | 0 <= `grade` <= `max_grade` |
| Type | Must be integer (whole number) |

### Additional Data

| Check | Rule |
|-------|------|
| Declared exists | Every manifest-declared attribute has a key |
| No undeclared | No keys exist that aren't declared |
| Warnings | Non-registry, non-`x-` attributes emit warning |

## Error Categories

### EDFStructureError

Missing required files.

### EDFConsistencyError

Cross-file data mismatches.

### EDFValidationError

Data validation failures. Has `errors: list[str]` with specifics.

## Validation Order

Recommended order for clear error messages:

1. Structural (files exist)
2. Schema (JSON parses, required fields present)
3. Consistency (cross-file matches)
4. Data (distributions, grades, attributes)
