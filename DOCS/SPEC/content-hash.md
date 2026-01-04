# Content Hash Algorithm

> **Navigation**: [Spec](README.md) | [manifest](manifest.md) | [validation](validation.md)

The `content_hash` field in manifest.json is computed using a deterministic algorithm that ensures identical content produces identical hashes.

## Algorithm

1. **Collect files** that contribute to the hash:
   - `task/rubric.md` (if `has_rubric=true`)
   - `task/prompt.md` (if `has_prompt=true`)
   - All submission content files: `content.md`, `content.pdf`, or `pages/*.jpg`

2. **Sort paths** alphabetically (lexicographic byte order)

3. **For each file** in sorted order, append to a byte buffer:
   - File path (UTF-8 encoded)
   - Null byte (0x00)
   - Raw file contents
   - Null byte (0x00)

4. **Compute SHA-256** hash of the concatenated buffer

5. **Format result** as `"sha256:"` + 64-char lowercase hex digest

## Example

Given an archive containing:
- `task/rubric.md` (content: `"# Rubric\n"`)
- `submissions/alice/content.md` (content: `"Answer A\n"`)
- `submissions/bob/content.md` (content: `"Answer B\n"`)

### Step 1: Sorted paths

```
submissions/alice/content.md
submissions/bob/content.md
task/rubric.md
```

### Step 2: Buffer contents

```
submissions/alice/content.md\x00Answer A\n\x00submissions/bob/content.md\x00Answer B\n\x00task/rubric.md\x00# Rubric\n\x00
```

(where `\x00` = null byte)

### Step 3: SHA-256

Hash the buffer to produce the `content_hash` value.

## Rationale

**Null separators**: Prevent ambiguity between file paths and contents.

**Sorting**: Ensures deterministic ordering regardless of filesystem traversal.

**Content files only**: Hash changes only when grading content changes, not when metadata updates.

## Files NOT Included

These files are excluded from the hash:
- `manifest.json`
- `task/core.json`
- `task/additional_data.json`
- `submissions/_index.json`
- `submissions/{id}/core.json`
- `submissions/{id}/additional_data.json`

This allows metadata updates without changing the content hash.
