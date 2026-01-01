# Specification for the Edexia Data Format (.edf), v0

Note that justifications for technical decisions are marked with [<integer>].

## 1. Overview

An .edf file is a ZIP archive [1] containing all information necessary for an ALS package to grade student submissions. One .edf file represents one task, which corresponds to one rubric or grading prompt [2].

A task may contain multiple submissions. Data within an .edf file falls into two categories: core data, which is required for every file, and additional data, which is optional and declared per-file.

An .edf file, once created, should have immutable data. Modification of data should result in a new .edf file with a new version hash. Downstream ALS systems should prefer higher version numbers for the same task_id.

## 2. Grades

All grades must be represented as integers. This applies to the ground truth grade and to the grade distributions.

For grading schemes that do not naturally produce integers, the following conversions apply. Letter grades should be mapped to integers (for example, A=4, B=3, C=2, D=1, F=0). Half-mark systems should be scaled by multiplication (for example, a 0-10 scale with half-marks becomes 0-20, where 7.5 becomes 15).

JSON does not distinguish between integers and floating-point numbers. Implementations must validate that grade values are whole numbers and reject or round non-integers as appropriate.

## 3. Folder Structure

```
task.edf
├── manifest.json
├── task/
│   ├── core.json
│   ├── additional_data.json
│   ├── rubric.md
│   └── prompt.md
└── submissions/
    ├── _index.json
    └── {submission_id}/
        ├── core.json
        ├── additional_data.json
        ├── content.md
        ├── content.pdf
        └── pages/
            ├── 0.jpg
            └── ...
```

The manifest.json file is required. The task/core.json file is required. The submissions/_index.json file is required. Each submission folder must contain a core.json file.

The task/additional_data.json file must be present if and only if task-level additional data attributes are declared in the manifest. The same rule applies to submission-level additional_data.json files.

The rubric.md file must be present if has_rubric is true in the manifest. The prompt.md file must be present if has_prompt is true in the manifest.

Each submission must contain exactly one of: content.md (for markdown/text), content.pdf (for PDF), or a pages/ directory containing numbered JPEG images starting from 0.jpg. The content format must match the content_format declared in the manifest.

## 4. File Specifications

### 4.1 manifest.json

The manifest declares the structure and contents of the entire package.

```json
{
  "edf_version": "1.0.0",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "content_hash": "sha256:...",
  "created_at": 1736942400000,
  "content_format": "markdown",
  "submission_count": 150,
  "has_rubric": true,
  "has_prompt": false,
  "additional_data": {
    "task": ["school_id", "subject_code"],
    "submission": ["student_name", "grader_id"]
  }
}
```

The edf_version field uses semantic versioning. The task_id is a UUID v4 that permanently identifies this task and never changes. The content_hash is a SHA256 hash of all content files, prefixed with "sha256:". The created_at field is a Unix millisecond timestamp.

The content_format field must be one of "markdown", "pdf", or "images". All submissions within the file must use this format.

The additional_data object declares which additional data attributes are used at the task level and submission level. If no additional data is used at a given level, the corresponding array should be empty.

### 4.2 task/core.json

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "version": 1,
  "max_grade": 20
}
```

The task_id must match the manifest. The version is an integer that increments whenever the task content changes. The max_grade is an integer representing the maximum possible grade; valid grades range from 0 to max_grade inclusive.

### 4.3 task/additional_data.json

This file contains the values for all task-level additional data attributes declared in the manifest. Every declared attribute must have a corresponding key. Values may be null if unknown.

```json
{
  "school_id": "VIC-12345",
  "subject_code": "VCE-MATH-METHODS"
}
```

### 4.4 submissions/_index.json

```json
{
  "submission_ids": ["student_a_2024", "student_b_2024", "student_c_2024"]
}
```

This file lists all submission IDs present in the submissions directory. The length of submission_ids must equal submission_count in the manifest.

### 4.5 submissions/{id}/core.json

```json
{
  "submission_id": "student_a_2024",
  "grade": 15,
  "grade_distributions": {
    "optimistic": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.05, 0.15, 0.5, 0.2, 0.1, 0, 0, 0],
    "expected": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.4, 0.2, 0.1, 0, 0, 0],
    "pessimistic": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0.2, 0.3, 0.25, 0.1, 0.05, 0, 0, 0]
  }
}
```

The submission_id must match the folder name and must consist only of alphanumeric characters and underscores.

The grade is an integer representing the ground truth grade. It must be in the range [0, max_grade].

The grade_distributions object contains three probability distributions: optimistic, expected, and pessimistic. Each distribution is an array of probabilities where the array length equals max_grade + 1. The value at index i represents the probability of receiving grade i. All probabilities must be non-negative and must sum to 1.0 (with allowance for floating-point tolerance).

The three distributions model different levels of noise in human marker behavior:

- **optimistic**: Low-noise scenario. Assumes markers grade consistently with minimal variation. Use a tighter distribution (lower spread/variance).
- **expected**: Medium-noise scenario. The baseline prediction representing typical marker variability.
- **pessimistic**: High-noise scenario. Assumes markers exhibit significant inconsistency. Use a wider distribution (higher spread/variance) that accounts for greater uncertainty.

These modes do NOT represent systematic biases (e.g., "harsh" vs "lenient" graders). They model the degree of randomness/noise in the grading process. A low-noise grader produces predictable grades; a high-noise grader's grades vary unpredictably even for similar work.

### 4.6 submissions/{id}/additional_data.json

This file contains the values for all submission-level additional data attributes declared in the manifest. Every declared attribute must have a corresponding key. Values may be null if unknown.

```json
{
  "student_name": "Alice Smith",
  "grader_id": "teacher_jane"
}
```

## 5. Content Hash Algorithm

The content_hash field in the manifest is computed using a deterministic algorithm that ensures identical content produces identical hashes regardless of when or where the file is created.

### 5.1 Algorithm

1. Collect all files that contribute to the content hash:
   - task/rubric.md (if has_rubric is true)
   - task/prompt.md (if has_prompt is true)
   - All submission content files: content.md, content.pdf, or pages/*.jpg

2. Sort the collected file paths alphabetically (lexicographic byte order).

3. For each file in sorted order, append to a byte buffer:
   - The file path encoded as UTF-8
   - A null byte (0x00)
   - The raw file contents
   - A null byte (0x00)

4. Compute the SHA-256 hash of the concatenated buffer.

5. Format the result as "sha256:" followed by the 64-character lowercase hexadecimal digest.

### 5.2 Example

Given an archive containing:
- task/rubric.md (content: "# Rubric\n")
- submissions/alice/content.md (content: "Answer A\n")
- submissions/bob/content.md (content: "Answer B\n")

The sorted paths are:
1. submissions/alice/content.md
2. submissions/bob/content.md
3. task/rubric.md

The buffer contents (shown with \x00 as null bytes):
```
submissions/alice/content.md\x00Answer A\n\x00submissions/bob/content.md\x00Answer B\n\x00task/rubric.md\x00# Rubric\n\x00
```

The SHA-256 hash of this buffer produces the content_hash value.

### 5.3 Rationale

The null byte separators prevent ambiguity between a file path that ends with certain characters and file contents that begin with those characters. Sorting ensures deterministic ordering regardless of filesystem traversal order. Including only content files (not metadata like core.json) means the hash changes only when actual grading content changes, not when metadata is updated.

## 6. Additional Data Registry

The additional data registry is a document maintained alongside this specification. It defines the canonical names, types, and semantics for additional data attributes.

The purpose of the registry is to prevent different teams from inventing different names for the same concept. Before introducing a new attribute, developers should consult the registry to determine whether an existing attribute serves the same purpose.

### 6.1 Registry Format

The registry is structured as follows:

```yaml
task_level:
  school_id:
    type: string
    description: Identifier for the school or institution
    added_in: 0.1.0

submission_level:
  student_name:
    type: string
    description: Human-readable student name
    added_in: 0.1.0
```

Since JSON does not distinguish integers from floating-point numbers, attributes with integer semantics are typed as "number" with a note that values must be whole numbers.

### 6.2 Standard Task-Level Attributes

school_id (string): Identifier for the school or institution.

subject_code (string): Subject identifier, such as "VCE-MATH-METHODS".

time_limit_minutes (number): Time allowed for task completion, in integer minutes.

academic_year (string): Academic year, such as "2024".

difficulty_level (string): One of "easy", "medium", or "hard".

source_exam (string): Name or identifier of the source examination.

section_id (string): Section within a larger exam.

### 6.3 Standard Submission-Level Attributes

**llm_context (string): Per-submission context required for accurate LLM grading.** This is the primary mechanism for providing submission-specific information that an LLM grader needs but cannot infer from the content alone. Examples include:
- The specific question or prompt the student answered (when submissions contain only answers)
- OCR confidence warnings or transcription notes for handwritten submissions
- Accommodation notes (e.g., "student has dyslexia - do not penalize spelling")
- Language context (e.g., "student is ESL - focus on content over grammar")
- Any per-student variation in grading criteria

This attribute is essential for LLM-based grading systems where context varies per submission.

student_name (string): Human-readable student name.

student_id (string): Institutional student identifier.

grader_id (string): Identifier for the human grader.

submitted_at (number): Unix millisecond timestamp indicating when the submission was received.

graded_at (number): Unix millisecond timestamp indicating when grading was completed.

time_taken_minutes (number): Actual time the student spent, in integer minutes.

attempt_number (number): For retakes, the attempt number as an integer (1, 2, 3, and so on).

marker_feedback (string): Free-text feedback from the grader.

### 6.4 Adding Attributes to the Registry

To add a new attribute, a developer opens an RFC containing the proposed name, type, description, and use case. Other teams review the proposal for one week. Maintainers then approve the proposal or suggest an existing attribute that serves the same purpose. Approved attributes are added to the registry.

This process imposes friction that encourages developers to search the registry before proposing new attributes.

### 6.5 Custom Attributes

For attributes that are specific to one team and do not belong in the shared registry, the x- prefix provides a namespace mechanism.

Custom attribute names must follow this pattern: x-{namespace}-{attribute}, where namespace is a reverse-domain identifier using hyphens (such as "edu-myschool") and attribute is a descriptive name.

```json
{
  "additional_data": {
    "submission": ["student_name", "x-edu-myschool-internal-audit-flag"]
  }
}
```

Custom attributes with the x- prefix may be used without RFC approval. If a custom attribute later proves useful to multiple teams, it may be proposed for inclusion in the registry without the x- prefix.

### 6.6 Attribute Resolution

When a reader encounters an attribute name, it should first check whether the name exists in the registry. If so, the registry defines the type and semantics. If the name begins with x-, it is a custom attribute and should be treated as an opaque value. If the name is neither registered nor prefixed with x-, implementations should emit a validation warning, as this likely indicates a typo or an unregistered attribute.

## 7. Timestamps

All timestamps use Unix millisecond format: the number of milliseconds since 1970-01-01 00:00:00 UTC.

For example, 1736942400000 represents 2025-01-15T12:00:00.000Z.

## 8. Validation

### 8.1 Structural Validation

The following files must exist: manifest.json, task/core.json, submissions/_index.json. For each submission ID listed in _index.json, a folder with that name must exist containing core.json.

If additional_data.task in the manifest is non-empty, task/additional_data.json must exist. If additional_data.submission in the manifest is non-empty, each submission folder must contain additional_data.json.

### 8.2 Consistency Validation

The submission_count in the manifest must equal the length of submission_ids in _index.json. The task_id in task/core.json must match the task_id in the manifest. Each submission_id in core.json must match its containing folder name.

### 8.3 Additional Data Validation

Every attribute declared in the manifest must have a corresponding key in the relevant additional_data.json file. No keys may appear in additional_data.json that are not declared in the manifest. Attribute names that are neither registered nor prefixed with x- should produce a warning.

### 8.4 Grade Distribution Validation

Each of the three required distributions (optimistic, expected, pessimistic) must be an array of length max_grade + 1. All values must be non-negative. The sum of values must equal 1.0, with allowance for floating-point tolerance (recommended: 0.0001).

The grade value must be an integer in the range [0, max_grade].

## 9. Defense

[1] ZIP is chosen over SQLite because it is easy to unzip and use grep or similar tools for ad-hoc data inspection. ZIP is chosen over a single JSON file because ZIP supports range requests, allowing partial extraction from very large archives. ZIP is chosen over CSV because binary data such as images and PDFs do not fit naturally in CSV. ZIP is chosen over protobuf because protobufs require specialised tooling to inspect.

[2] Defining one .edf as one rubric leads to counterintuitive scenarios. One assessment may produce multiple .edf files if different sections are graded differently. Conversely, different exam questions may share one .edf file if they use the same rubric. This trade-off is accepted because mixing different grading schemes within a single file introduces complexity that outweighs the inconvenience of multiple files.
