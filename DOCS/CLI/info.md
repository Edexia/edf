# edf info

> **Navigation**: [CLI](README.md) | [validate](validate.md) | [view](view.md)

Show summary information about an EDF file.

## Usage

```bash
edf info <file> [--dangerously-load-unzipped]
```

## Options

| Option | Description |
|--------|-------------|
| `--dangerously-load-unzipped` | Load from an unzipped directory |

## Example Output

```bash
$ edf info assignment.edf
EDF Version:    1.0.0
Task ID:        550e8400-e29b-41d4-a716-446655440000
Version:        1
Content Hash:   sha256:a1b2c3d4e5f6...
Created:        1736942400000
Content Format: markdown
Max Grade:      20
Submissions:    150
Has Rubric:     True
Has Prompt:     True
Task Attrs:     school_id, subject_code
Sub Attrs:      student_name, grader_id
```

## Output Fields

| Field | Description |
|-------|-------------|
| EDF Version | Format version (semver) |
| Task ID | UUID v4 identifier |
| Version | Task version number |
| Content Hash | SHA256 hash of content |
| Created | Unix millisecond timestamp |
| Content Format | `markdown`, `pdf`, or `images` |
| Max Grade | Maximum possible grade |
| Submissions | Number of submissions |
| Has Rubric | Whether rubric.md exists |
| Has Prompt | Whether prompt.md exists |
| Task Attrs | Task-level additional data |
| Sub Attrs | Submission-level additional data |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | File not found or read error |

## Unzipped Directory

When using `--dangerously-load-unzipped`:

```bash
$ edf info ./task_dir/ --dangerously-load-unzipped
** EPHEMERAL EDF (loaded from directory) **
EDF Version:    1.0.0
Task ID:        00000000-0000-0000-0000-000000000000
Version:        0
Content Hash:   N/A
...
```

The ephemeral markers indicate this is not a versioned EDF.
