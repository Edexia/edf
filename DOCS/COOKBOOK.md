# EDF Cookbook

> **Navigation**: [README](../README.md) | [Overview](OVERVIEW.md) | [CLI](CLI/README.md) | [SDK](SDK/README.md) | [Spec](SPEC/README.md)

Quick recipes for common tasks. Each recipe links to detailed documentation.

---

## Create an EDF File

```python
from edf import EDF

edf = EDF(max_grade=20)
edf.rubric = "# Criteria\n- Correctness: 10pts\n- Style: 10pts"

# Note: this applies only if there is no per-student level context (such as what question they answered)
edf.add_submission(
    submission_id="alice",
    grade=15,
    optimistic=[0]*13 + [0.05, 0.15, 0.5, 0.2, 0.1, 0, 0, 0],
    expected=[0]*13 + [0.1, 0.2, 0.4, 0.2, 0.1, 0, 0, 0],
    pessimistic=[0]*12 + [0.1, 0.2, 0.3, 0.25, 0.1, 0.05, 0, 0, 0],
    content="Student answer here...",
)

edf.save("output.edf")
```

**Details**: [SDK/EDF.md](SDK/EDF.md#add_submission)

---

## Read an EDF File

```python
from edf import EDF

with EDF.open("assignment.edf") as edf:
    print(f"Task: {edf.task_id}, Max: {edf.max_grade}")
    for sub in edf.submissions:
        print(f"  {sub.id}: {sub.grade}")
```

**Details**: [SDK/EDF.md](SDK/EDF.md#edfopen)

---

## Validate a File

### CLI
```bash
edf validate assignment.edf
```

### Python
```python
from edf import EDF, EDFValidationError

try:
    with EDF.open("file.edf", validate=True) as edf:
        print("Valid!")
except EDFValidationError as e:
    for error in e.errors:
        print(f"  - {error}")
```

**Details**: [CLI/validate.md](CLI/validate.md) | [SDK/exceptions.md](SDK/exceptions.md)

---

## View a File in Browser

```bash
edf view assignment.edf
edf view assignment.edf -p 3000  # custom port
```

**Details**: [CLI/view.md](CLI/view.md)

---

## Get File Info

```bash
edf info assignment.edf
```

**Details**: [CLI/info.md](CLI/info.md)

---

## Add LLM Grading Context

```python
edf.add_submission(
    submission_id="bob",
    grade=12,
    optimistic=[...], expected=[...], pessimistic=[...],
    content="OCR transcription of handwritten work...",
    llm_context="""
Question: Q3 - Explain photosynthesis.
OCR confidence: 87%. Student has dyslexia accommodation.
""",
)
```

**Details**: [SDK/EDF.md](SDK/EDF.md#add_submission) | [SPEC/additional-data.md](SPEC/additional-data.md#llm_context)

---

## Add Metadata

```python
# Task-level
edf.set_task_data(school_id="SCHOOL-001", subject_code="CS-101")

# Submission-level (via **kwargs)
edf.add_submission(
    ...,
    student_name="Alice Smith",
    student_id="2025-042",
)
```

**Details**: [SDK/EDF.md](SDK/EDF.md#set_task_data) | [SPEC/additional-data.md](SPEC/additional-data.md)

---

## Work with PDF/Image Submissions

```python
# PDF
with open("work.pdf", "rb") as f:
    edf.add_submission(..., content=f.read())

# Images (list of JPEG bytes)
pages = [open(f"page_{i}.jpg", "rb").read() for i in range(3)]
edf.add_submission(..., content=pages)
```

**Details**: [SDK/Submission.md](SDK/Submission.md#content-access-methods)

---

## Batch Validate Multiple Files

```bash
for f in *.edf; do
    edf validate "$f" || echo "FAILED: $f"
done
```

**Details**: [CLI/validate.md](CLI/validate.md)
