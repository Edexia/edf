# manifest.json

> **Navigation**: [Spec](README.md) | [task](task.md) | [submissions](submissions.md)

The manifest declares the structure and contents of the entire package.

## Schema

```json
{
  "edf_version": "1.0.0",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "content_hash": "sha256:...",
  "created_at": 1736942400000,
  "content_format": "markdown",
  "submission_count": 150,
  "has_rubric": true,
  "has_prompt": false,
  "additional_data": {
    "task": ["school_id", "subject_code"],
    "submission": ["student_name", "grader_id"]
  }
}
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `edf_version` | string | Yes | Format version (semver) |
| `task_id` | string | Yes | UUID v4, permanently identifies task |
| `content_hash` | string | Yes | SHA256 hash, prefixed "sha256:" |
| `created_at` | number | Yes | Unix millisecond timestamp |
| `content_format` | string | Yes | One of: "markdown", "pdf", "images" |
| `submission_count` | number | Yes | Number of submissions |
| `has_rubric` | boolean | Yes | Whether rubric.md exists |
| `has_prompt` | boolean | Yes | Whether prompt.md exists |
| `additional_data` | object | Yes | Declared attributes |

## additional_data Object

Declares which additional data attributes are used:

```json
{
  "additional_data": {
    "task": ["school_id", "subject_code"],
    "submission": ["student_name", "llm_context"]
  }
}
```

- `task`: Attributes in `task/additional_data.json`
- `submission`: Attributes in each `submissions/{id}/additional_data.json`

Use empty arrays if no additional data:

```json
{
  "additional_data": {
    "task": [],
    "submission": []
  }
}
```

## content_format Values

| Value | Content File | Description |
|-------|--------------|-------------|
| `"markdown"` | `content.md` | Plain text/markdown |
| `"pdf"` | `content.pdf` | PDF document |
| `"images"` | `pages/0.jpg`, ... | Numbered JPEGs |

All submissions must use the same format.

## Validation Rules

- `edf_version` must be valid semver
- `task_id` must be UUID v4 format
- `content_hash` must start with "sha256:"
- `submission_count` must match `_index.json` length
- `has_rubric=true` requires `task/rubric.md` to exist
- `has_prompt=true` requires `task/prompt.md` to exist
- All declared attributes must exist in corresponding files
