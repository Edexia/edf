# EDF Command Line Interface

This document covers the CLI tool for working with EDF files. For the Python SDK, see [SDK.md](SDK.md). For the file format specification, see [SPEC.md](SPEC.md).

## Installation

### Using uv (recommended)

```bash
# Install globally as a tool
uv tool install git+https://github.com/Edexia/edf

# Or run directly without installing
uvx --from git+https://github.com/Edexia/edf edf <command>
```

### Using pip

```bash
pip install git+https://github.com/Edexia/edf
```

### From source

```bash
git clone https://github.com/Edexia/edf
cd edf
uv sync
uv run edf <command>
```

---

## Commands

### edf info

Show summary information about an EDF file.

```bash
edf info <file> [--dangerously-load-unzipped]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--dangerously-load-unzipped` | Load from an unzipped directory instead of a .edf file |

**Example:**

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

**Output fields:**

| Field | Description |
|-------|-------------|
| EDF Version | Format version (semver) |
| Task ID | UUID v4 identifier for the task |
| Version | Task version number |
| Content Hash | SHA256 hash of content files |
| Created | Unix millisecond timestamp |
| Content Format | One of: markdown, pdf, images |
| Max Grade | Maximum possible grade |
| Submissions | Number of submissions |
| Has Rubric | Whether rubric.md is present |
| Has Prompt | Whether prompt.md is present |
| Task Attrs | Task-level additional data attributes |
| Sub Attrs | Submission-level additional data attributes |

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | File not found or read error |

---

### edf validate

Validate an EDF file and report any errors.

```bash
edf validate <file> [--dangerously-load-unzipped]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--dangerously-load-unzipped` | Load from an unzipped directory (skips hash validation) |

**Example (valid file):**

```bash
$ edf validate assignment.edf
Valid: assignment.edf
  Task ID: 550e8400-e29b-41d4-a716-446655440000
  Submissions: 150
```

**Example (invalid file):**

```bash
$ edf validate broken.edf
Invalid: broken.edf
  - Missing required file: task/core.json
  - Submission count mismatch: manifest says 10, index has 8
```

**Validation checks:**

1. **Structural validation**
   - Required files exist (manifest.json, task/core.json, submissions/_index.json)
   - Submission folders match declared IDs
   - Additional data files present when declared

2. **Consistency validation**
   - Task ID matches between manifest and task/core.json
   - Submission count matches between manifest and index
   - Submission IDs match folder names

3. **Data validation**
   - Grade distributions have correct length (max_grade + 1)
   - Distributions sum to 1.0 (within tolerance)
   - Grades are within valid range [0, max_grade]
   - Additional data attributes match declarations

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | File is valid |
| 1 | File not found, read error, or validation failed |

---

### edf view

Start an interactive web viewer for an EDF file.

```bash
edf view <file> [--port PORT] [--no-browser]
```

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--port` | `-p` | 8080 | Port to serve on |
| `--no-browser` | | | Don't open browser automatically |

**Example:**

```bash
$ edf view assignment.edf
Starting EDF viewer for: /path/to/assignment.edf
Open http://localhost:8080 in your browser
Press Ctrl+C to stop
```

**Port conflict handling:**

If the requested port is already in use, the viewer automatically finds the next available port:

```bash
$ edf view assignment.edf -p 8080
Starting EDF viewer for: /path/to/assignment.edf
Port 8080 in use, using port 8081
Open http://localhost:8081 in your browser
Press Ctrl+C to stop
```

The viewer tries up to 100 consecutive ports starting from the requested port.

**Viewer features:**

- Browse all submissions in the file
- View submission content (markdown, PDF, or images)
- See grade distributions visualized
- Inspect metadata and additional data
- Range request support for efficient loading of large files

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Server stopped normally (Ctrl+C) |
| 1 | File not found or server error |

---

## Examples

### Quick file inspection

```bash
# Get a summary of the file
edf info exam_results.edf

# Check if file is valid before processing
edf validate exam_results.edf && echo "Ready to process"
```

### Batch validation

```bash
# Validate all EDF files in a directory
for f in *.edf; do
    edf validate "$f" || echo "FAILED: $f"
done
```

### Viewing on a specific port

```bash
# Use port 3000 for the viewer
edf view submissions.edf -p 3000

# Don't auto-open browser (useful for remote servers)
edf view submissions.edf --no-browser
```

### Integration with other tools

```bash
# Extract info for scripting
edf info data.edf | grep "Submissions:" | awk '{print $2}'

# Validate before upload
edf validate export.edf && aws s3 cp export.edf s3://bucket/
```

---

## Troubleshooting

### "File not found" error

Ensure the path is correct and the file exists:

```bash
ls -la assignment.edf
```

### "Port already in use"

The viewer automatically handles this by finding an available port. If you need a specific port, stop the process using it:

```bash
# Find what's using port 8080
lsof -i :8080

# Kill the process if needed
kill <PID>
```

### Validation errors

Run `edf validate` to see specific issues:

```bash
edf validate broken.edf
```

Common issues:
- Missing required files in the archive
- Mismatched submission counts
- Invalid grade distributions (wrong length or don't sum to 1.0)
- Undeclared additional data attributes

### Large file performance

The viewer uses HTTP range requests for efficient loading. For very large files (>1GB), consider:
- Using `edf info` for quick inspection without loading content
- Running the viewer locally rather than over a network

---

## Working with Unzipped Directories

For development and testing, you can work directly with unzipped EDF directories using the `--dangerously-load-unzipped` flag.

### Workflow

```bash
# 1. Unzip an existing EDF
unzip task.edf -d ./task_dir/

# 2. Edit files directly (e.g., in VS Code)
code ./task_dir/

# 3. View info without re-zipping
edf info ./task_dir/ --dangerously-load-unzipped

# 4. Validate structure (hash validation skipped)
edf validate ./task_dir/ --dangerously-load-unzipped
```

### Output

When using `--dangerously-load-unzipped`, the output indicates ephemeral status:

```bash
$ edf info ./task_dir/ --dangerously-load-unzipped
** EPHEMERAL EDF (loaded from directory) **
EDF Version:    1.0.0
Task ID:        00000000-0000-0000-0000-000000000000
Version:        0
Content Hash:   N/A
Created:        None
...
```

### Limitations

- The `edf view` command does not support unzipped directories
- Hash validation is skipped (the content hash can't be verified without re-computing it)
- The ephemeral `task_id` and `version=0` indicate this is not a versioned EDF
