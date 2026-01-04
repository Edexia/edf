# Submission Class

> **Navigation**: [SDK](README.md) | [EDF](EDF.md) | [GradeDistributions](GradeDistributions.md)

A submission within an EDF file.

## Properties

| Property | Type | Description |
|----------|------|-------------|
| `id` | `str` | Submission identifier |
| `grade` | `int` | Ground truth grade |
| `distributions` | `GradeDistributions` | The three distributions |
| `content` | `str \| bytes \| list[bytes]` | Raw content |
| `additional` | `dict[str, Any]` | Submission metadata |
| `content_format` | `ContentFormat` | Detected format |

## Content Access Methods

### get_markdown

```python
submission.get_markdown() -> str | None
```

Returns markdown content, or `None` if not markdown format.

```python
with EDF.open("file.edf") as edf:
    sub = edf.get_submission("alice")
    if text := sub.get_markdown():
        print(text)
```

### get_pdf

```python
submission.get_pdf() -> bytes | None
```

Returns PDF bytes, or `None` if not PDF format.

```python
if pdf_bytes := sub.get_pdf():
    with open("output.pdf", "wb") as f:
        f.write(pdf_bytes)
```

### get_images

```python
submission.get_images() -> list[bytes] | None
```

Returns list of JPEG bytes, or `None` if not images format.

```python
if images := sub.get_images():
    for i, img_bytes in enumerate(images):
        with open(f"page_{i}.jpg", "wb") as f:
            f.write(img_bytes)
```

## Accessing Additional Data

```python
with EDF.open("file.edf") as edf:
    sub = edf.get_submission("alice")

    # Access via dict
    print(sub.additional.get("student_name"))
    print(sub.additional.get("llm_context"))
```

## Example: Iterate All Submissions

```python
with EDF.open("assignment.edf") as edf:
    for sub in edf.submissions:
        print(f"ID: {sub.id}")
        print(f"  Grade: {sub.grade}/{edf.max_grade}")
        print(f"  Format: {sub.content_format}")

        if text := sub.get_markdown():
            print(f"  Content preview: {text[:100]}...")
```
