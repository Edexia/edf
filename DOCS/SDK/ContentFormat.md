# ContentFormat Enum

> **Navigation**: [SDK](README.md) | [EDF](EDF.md) | [Submission](Submission.md)

Enum for content formats in EDF files.

## Values

```python
from edf import ContentFormat

ContentFormat.MARKDOWN  # "markdown"
ContentFormat.PDF       # "pdf"
ContentFormat.IMAGES    # "images"
```

## Format Detection

Content format is inferred from the type passed to `add_submission`:

| Python Type | ContentFormat | File(s) in Archive |
|-------------|---------------|-------------------|
| `str` | `MARKDOWN` | `content.md` |
| `bytes` | `PDF` | `content.pdf` |
| `list[bytes]` | `IMAGES` | `pages/0.jpg`, `pages/1.jpg`, ... |

## Constraint

All submissions in an EDF must use the same content format. Mixing formats raises an error.

## Checking Format

```python
from edf import EDF, ContentFormat

with EDF.open("file.edf") as edf:
    # EDF-level format
    if edf.content_format == ContentFormat.MARKDOWN:
        print("All submissions are markdown")

    # Submission-level format
    for sub in edf.submissions:
        if sub.content_format == ContentFormat.PDF:
            pdf_bytes = sub.get_pdf()
```

## Example: Handle Multiple Formats

```python
with EDF.open("file.edf") as edf:
    for sub in edf.submissions:
        match sub.content_format:
            case ContentFormat.MARKDOWN:
                text = sub.get_markdown()
                print(f"{sub.id}: {len(text)} chars")

            case ContentFormat.PDF:
                pdf = sub.get_pdf()
                print(f"{sub.id}: {len(pdf)} bytes PDF")

            case ContentFormat.IMAGES:
                images = sub.get_images()
                print(f"{sub.id}: {len(images)} pages")
```
