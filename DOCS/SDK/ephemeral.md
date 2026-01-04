# Ephemeral EDFs

> **Navigation**: [SDK](README.md) | [EDF](EDF.md)

For rapid iteration during development, you can load an unzipped EDF directory directly. This creates an "ephemeral" EDF that bypasses versioning and integrity checks.

## Loading from Directory

```python
from edf import EDF

# First, unzip an EDF manually:
#   unzip task.edf -d ./task_dir/

# Then load directly (requires explicit flag)
edf = EDF.from_directory("./task_dir/", dangerously_load_unzipped_edf=True)

# Ephemeral properties
print(edf.is_ephemeral)   # True
print(edf.task_id)        # "00000000-0000-0000-0000-000000000000"
print(edf.version)        # 0
print(edf.content_hash)   # None
print(edf.created_at)     # None
```

## Development Workflow

1. Unzip an EDF:
   ```bash
   unzip task.edf -d ./task_dir/
   ```

2. Edit files directly in `./task_dir/`:
   - Modify `submissions/student_1/content.md`
   - Add new submission folders
   - Edit rubric.md

3. Load and test:
   ```python
   edf = EDF.from_directory("./task_dir/", dangerously_load_unzipped_edf=True)
   ```

4. Repeat steps 2-3 as needed

## Saving Ephemeral EDFs

When you save an ephemeral EDF, it becomes a "real" EDF:

```python
edf = EDF.from_directory("./task_dir/", dangerously_load_unzipped_edf=True)
print(edf.is_ephemeral)  # True

edf.save("output.edf")   # Prints warning, generates new UUID

print(edf.is_ephemeral)  # False
print(edf.task_id)       # New UUID: "550e8400-e29b-41d4-..."
print(edf.version)       # 1
```

## is_ephemeral Property

Check if an EDF was loaded from an unzipped directory:

```python
# Created from scratch
edf1 = EDF(max_grade=10)
print(edf1.is_ephemeral)  # False

# Opened from file
with EDF.open("task.edf") as edf2:
    print(edf2.is_ephemeral)  # False

# Loaded from directory
edf3 = EDF.from_directory("./dir/", dangerously_load_unzipped_edf=True)
print(edf3.is_ephemeral)  # True
```

## Constants

```python
from edf import EPHEMERAL_TASK_ID, EPHEMERAL_VERSION

print(EPHEMERAL_TASK_ID)  # "00000000-0000-0000-0000-000000000000"
print(EPHEMERAL_VERSION)  # 0
```

## CLI Support

The CLI also supports unzipped directories:

```bash
edf info ./task_dir/ --dangerously-load-unzipped
edf validate ./task_dir/ --dangerously-load-unzipped
```

**Note**: `edf view` does not support unzipped directories.
