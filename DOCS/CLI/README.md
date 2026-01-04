# CLI Reference

> **Navigation**: [Home](../../README.md) | [Overview](../OVERVIEW.md) | [Cookbook](../COOKBOOK.md) | [SDK](../SDK/README.md) | [Spec](../SPEC/README.md)

Command line tools for working with EDF files.

## Installation

### Using uv (recommended)

```bash
# Install globally
uv tool install git+https://github.com/Edexia/edf

# Or run without installing
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

## Commands

| Command | Description | Details |
|---------|-------------|---------|
| `edf info` | Show file summary | [info.md](info.md) |
| `edf validate` | Validate a file | [validate.md](validate.md) |
| `edf view` | Interactive web viewer | [view.md](view.md) |

## Quick Examples

```bash
# Get file info
edf info assignment.edf

# Validate before processing
edf validate assignment.edf && echo "Ready"

# Open in browser
edf view assignment.edf
```

## Working with Unzipped Directories

For development, you can work with unzipped EDF directories:

```bash
# Unzip
unzip task.edf -d ./task_dir/

# Inspect without re-zipping
edf info ./task_dir/ --dangerously-load-unzipped

# Validate structure (hash validation skipped)
edf validate ./task_dir/ --dangerously-load-unzipped
```

**Note**: `edf view` does not support unzipped directories.
