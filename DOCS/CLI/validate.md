# edf validate

> **Navigation**: [CLI](README.md) | [info](info.md) | [view](view.md)

Validate an EDF file and report any errors.

## Usage

```bash
edf validate <file> [--dangerously-load-unzipped]
```

## Options

| Option | Description |
|--------|-------------|
| `--dangerously-load-unzipped` | Load from unzipped directory (skips hash validation) |

## Example Output

### Valid file

```bash
$ edf validate assignment.edf
Valid: assignment.edf
  Task ID: 550e8400-e29b-41d4-a716-446655440000
  Submissions: 150
```

### Invalid file

```bash
$ edf validate broken.edf
Invalid: broken.edf
  - Missing required file: task/core.json
  - Submission count mismatch: manifest says 10, index has 8
```

## Validation Checks

### Structural
- Required files exist (manifest.json, task/core.json, submissions/_index.json)
- Submission folders match declared IDs
- Additional data files present when declared

### Consistency
- Task ID matches between manifest and task/core.json
- Submission count matches between manifest and index
- Submission IDs match folder names

### Data
- Grade distributions have correct length (max_grade + 1)
- Distributions sum to 1.0 (within tolerance)
- Grades are in range [0, max_grade]
- Additional data attributes match declarations

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | File is valid |
| 1 | File not found, read error, or validation failed |

## Common Issues

| Error | Cause |
|-------|-------|
| Missing required file | Archive incomplete |
| Submission count mismatch | Manifest out of sync with _index.json |
| Distribution length wrong | Array length != max_grade + 1 |
| Distribution sum != 1.0 | Probabilities don't sum to 1 |
| Undeclared attribute | Additional data not in manifest |

## Batch Validation

```bash
for f in *.edf; do
    edf validate "$f" || echo "FAILED: $f"
done
```
