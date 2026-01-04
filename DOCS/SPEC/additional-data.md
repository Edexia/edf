# Additional Data Registry

> **Navigation**: [Spec](README.md) | [task](task.md) | [submissions](submissions.md)

The additional data registry defines canonical names, types, and semantics for metadata attributes.

## Purpose

Prevent different teams from inventing different names for the same concept. Before adding a new attribute, check if an existing one serves the purpose.

## Standard Task-Level Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `school_id` | string | School/institution identifier |
| `subject_code` | string | Subject ID (e.g., "VCE-MATH-METHODS") |
| `time_limit_minutes` | number | Time allowed (integer minutes) |
| `academic_year` | string | Academic year (e.g., "2024") |
| `difficulty_level` | string | "easy", "medium", or "hard" |
| `source_exam` | string | Source examination name |
| `section_id` | string | Section within larger exam |

## Standard Submission-Level Attributes

### llm_context (Important!)

Per-submission context for LLM grading. Essential when context varies between submissions.

```json
{
  "llm_context": "Question: Q3 - Explain photosynthesis.\nOCR confidence: 87%.\nStudent has dyslexia accommodation."
}
```

Use cases:
- Specific question/prompt the student answered
- OCR confidence warnings
- Accommodation notes (dyslexia, ESL, etc.)
- Any per-student grading variations

### Other Submission Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `student_name` | string | Human-readable name |
| `student_id` | string | Institutional ID |
| `grader_id` | string | Human grader identifier |
| `submitted_at` | number | Unix ms timestamp |
| `graded_at` | number | Unix ms timestamp |
| `time_taken_minutes` | number | Actual time spent (integer) |
| `attempt_number` | number | Retake number (1, 2, 3...) |
| `marker_feedback` | string | Free-text grader feedback |

## Custom Attributes

For team-specific attributes not in the registry, use the `x-` prefix:

```
x-{namespace}-{attribute}
```

Where `namespace` is a reverse-domain identifier using hyphens.

```json
{
  "additional_data": {
    "submission": ["student_name", "x-edu-myschool-internal-audit-flag"]
  }
}
```

Custom `x-` attributes don't require approval. If useful to others, propose for registry inclusion.

## Adding to Registry

1. Open an RFC with: name, type, description, use case
2. Other teams review for one week
3. Maintainers approve or suggest existing attribute
4. Approved attributes added to registry

## Validation Behavior

| Attribute Name | Behavior |
|----------------|----------|
| In registry | Use registry-defined type/semantics |
| Starts with `x-` | Treat as opaque custom value |
| Neither | Emit validation warning (likely typo) |
