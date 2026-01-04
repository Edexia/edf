# EDF Overview

> **Navigation**: [README](../README.md) | [Cookbook](COOKBOOK.md) | [CLI](CLI/README.md) | [SDK](SDK/README.md) | [Spec](SPEC/README.md)

## What is EDF?

EDF (Edexia Data Format) is a file format for packaging grading data used by automated learning systems. An `.edf` file is a ZIP archive containing:

- One grading task (rubric, prompt, max grade)
- Multiple student submissions
- Ground truth grades and grade distribution predictions

## Core Concepts

### Task
A task represents one grading assignment with a single rubric. It defines:
- `max_grade`: The maximum possible score (integer)
- `rubric`: Grading criteria (optional markdown)
- `prompt`: The question or assignment (optional markdown)

### Submission
A submission is one student's work for a task. Each submission contains:
- `grade`: Ground truth grade (integer 0 to max_grade)
- `grade_distributions`: Three probability distributions (optimistic, expected, pessimistic)
- `content`: The student work (markdown, PDF, or images)

### Grade Distributions
Each submission has three distributions modeling **marker noise levels**:
- **optimistic**: Low noise - markers grade consistently (tight distribution)
- **expected**: Medium noise - typical marker variability (baseline)
- **pessimistic**: High noise - markers are inconsistent (wide distribution)

These model variance/randomness, NOT systematic bias (harsh vs lenient).

## File Structure

```
task.edf (ZIP archive)
├── manifest.json           # Package metadata
├── task/
│   ├── core.json           # Task ID, version, max_grade
│   ├── rubric.md           # Grading criteria (optional)
│   └── prompt.md           # Assignment prompt (optional)
└── submissions/
    ├── _index.json         # List of submission IDs
    └── {submission_id}/
        ├── core.json       # Grade and distributions
        └── content.md      # Student work
```

## Immutability

EDF files are designed to be immutable. When content changes:
1. A new version is created
2. A new content hash is computed
3. The version number increments

Downstream systems should prefer higher version numbers for the same `task_id`.

## When to Use EDF

Use EDF when you need to:
- Package grading data for ML training
- Exchange graded submissions between systems
- Store ground truth grades with uncertainty estimates
- Archive assessment data in a portable format

## Next Steps

- [Cookbook](COOKBOOK.md) - Quick recipes for common tasks
- [CLI Reference](CLI/README.md) - Command line tools
- [SDK Reference](SDK/README.md) - Python library
- [Format Specification](SPEC/README.md) - Technical details
