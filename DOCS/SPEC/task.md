# Task Files

> **Navigation**: [Spec](README.md) | [manifest](manifest.md) | [submissions](submissions.md)

Files in the `task/` directory.

## task/core.json

Required. Contains task identification and grading configuration.

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "version": 1,
  "max_grade": 20
}
```

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Must match manifest |
| `version` | number | Integer, increments on content change |
| `max_grade` | number | Integer, maximum possible grade |

Valid grades range from 0 to `max_grade` inclusive.

## task/additional_data.json

Required if `additional_data.task` in manifest is non-empty. Contains values for all declared task-level attributes.

```json
{
  "school_id": "VIC-12345",
  "subject_code": "VCE-MATH-METHODS"
}
```

### Rules

- Every declared attribute must have a key
- Values may be `null` if unknown
- No undeclared keys allowed

## task/rubric.md

Required if `has_rubric=true` in manifest. Contains grading criteria in markdown.

```markdown
# Grading Rubric

## Correctness (10 points)
- Full marks: Correct answer with clear working
- Half marks: Correct approach, minor errors
- No marks: Incorrect approach

## Style (10 points)
- Full marks: Clear, well-organized
- Half marks: Some clarity issues
- No marks: Unclear or disorganized
```

## task/prompt.md

Required if `has_prompt=true` in manifest. Contains the assignment question/task in markdown.

```markdown
# Assignment: String Reversal

Write a Python function that reverses a string without using
built-in reverse methods.

## Requirements
- Function signature: `def reverse(s: str) -> str`
- Must handle empty strings
- Must handle Unicode characters

## Example
Input: "hello"
Output: "olleh"
```

## Directory Structure

```
task/
├── core.json              # Required
├── additional_data.json   # If declared
├── rubric.md              # If has_rubric=true
└── prompt.md              # If has_prompt=true
```
