# EDF Specification

> **Navigation**: [Home](../../README.md) | [Overview](../OVERVIEW.md) | [Cookbook](../COOKBOOK.md) | [CLI](../CLI/README.md) | [SDK](../SDK/README.md)

Technical specification for the Edexia Data Format (.edf).

## Format Overview

An `.edf` file is a ZIP archive containing all information necessary for an automated learning system to grade student submissions. One file represents one task (one rubric).

### Why ZIP?

- Easy to inspect with standard tools (`unzip`, `grep`)
- Supports range requests for partial extraction
- Handles binary content (images, PDFs) naturally
- No specialized tooling required

## Specification Topics

| Topic | Description | Details |
|-------|-------------|---------|
| Manifest | Package metadata | [manifest.md](manifest.md) |
| Task Files | Task configuration | [task.md](task.md) |
| Submissions | Submission data | [submissions.md](submissions.md) |
| Content Hash | Integrity verification | [content-hash.md](content-hash.md) |
| Additional Data | Metadata registry | [additional-data.md](additional-data.md) |
| Validation | Validation rules | [validation.md](validation.md) |

## Grades as Integers

All grades must be integers. Conversions:
- Letter grades: A=4, B=3, C=2, D=1, F=0
- Half-marks: Multiply scale (0-10 with halves becomes 0-20)

## Immutability

EDF files are designed to be immutable:
- Content changes create a new version
- New content hash is computed
- Version number increments

Downstream systems should prefer higher version numbers for the same `task_id`.

## Timestamps

All timestamps use Unix milliseconds (ms since 1970-01-01 00:00:00 UTC).

Example: `1736942400000` = 2025-01-15T12:00:00.000Z

## File Structure

```
task.edf
├── manifest.json           # Required
├── task/
│   ├── core.json           # Required
│   ├── additional_data.json
│   ├── rubric.md
│   └── prompt.md
└── submissions/
    ├── _index.json         # Required
    └── {submission_id}/
        ├── core.json       # Required
        ├── additional_data.json
        └── content.md | content.pdf | pages/
```

## Quick Links

- [manifest.json schema](manifest.md)
- [Grade distributions](submissions.md#grade-distributions)
- [Content hash algorithm](content-hash.md)
- [Standard attributes](additional-data.md#standard-attributes)
