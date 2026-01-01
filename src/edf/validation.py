"""Validation functions for EDF files."""

from zipfile import ZipFile
from typing import Any
from edf.models import (
    Manifest,
    TaskCore,
    SubmissionCore,
    SubmissionIndex,
    ContentFormat,
)
from edf.exceptions import (
    EDFStructureError,
    EDFConsistencyError,
    EDFValidationError,
)


# Known registered attributes per the spec
REGISTERED_TASK_ATTRIBUTES = {
    "school_id",
    "subject_code",
    "time_limit_minutes",
    "academic_year",
    "difficulty_level",
    "source_exam",
    "section_id",
}

REGISTERED_SUBMISSION_ATTRIBUTES = {
    "student_name",
    "student_id",
    "grader_id",
    "submitted_at",
    "graded_at",
    "time_taken_minutes",
    "attempt_number",
    "marker_feedback",
    "llm_context",  # Per-submission context for LLM grading (e.g., OCR warnings, dyslexia accommodations, question attempted)
}


def validate_structure(zf: ZipFile, manifest: Manifest) -> list[str]:
    """
    Validate that all required files exist in the archive.

    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    names = set(zf.namelist())

    # Required files
    required = ["manifest.json", "task/core.json", "submissions/_index.json"]
    for path in required:
        if path not in names:
            errors.append(f"Missing required file: {path}")

    # Conditional files based on manifest
    if manifest.has_rubric and "task/rubric.md" not in names:
        errors.append("manifest.has_rubric is true but task/rubric.md is missing")
    if manifest.has_prompt and "task/prompt.md" not in names:
        errors.append("manifest.has_prompt is true but task/prompt.md is missing")

    # Task additional data
    if manifest.additional_data.task:
        if "task/additional_data.json" not in names:
            errors.append(
                "manifest declares task additional_data but task/additional_data.json is missing"
            )
    else:
        if "task/additional_data.json" in names:
            errors.append(
                "task/additional_data.json exists but no task additional_data declared in manifest"
            )

    return errors


def validate_submission_structure(
    zf: ZipFile,
    manifest: Manifest,
    submission_ids: list[str],
) -> list[str]:
    """
    Validate that all submission folders have required files.

    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    names = set(zf.namelist())
    has_submission_additional = bool(manifest.additional_data.submission)

    for sid in submission_ids:
        base = f"submissions/{sid}/"

        # core.json required
        if f"{base}core.json" not in names:
            errors.append(f"Missing {base}core.json")

        # additional_data.json conditional
        has_additional = f"{base}additional_data.json" in names
        if has_submission_additional and not has_additional:
            errors.append(
                f"manifest declares submission additional_data but {base}additional_data.json is missing"
            )
        elif not has_submission_additional and has_additional:
            errors.append(
                f"{base}additional_data.json exists but no submission additional_data declared in manifest"
            )

        # Content files - exactly one of: content.md, content.pdf, pages/
        has_md = f"{base}content.md" in names
        has_pdf = f"{base}content.pdf" in names
        has_pages = any(n.startswith(f"{base}pages/") for n in names)

        content_count = sum([has_md, has_pdf, has_pages])
        if content_count == 0:
            errors.append(
                f"Submission {sid} has no content (need content.md, content.pdf, or pages/)"
            )
        elif content_count > 1:
            errors.append(
                f"Submission {sid} has multiple content types (should have exactly one)"
            )

        # Validate content format matches manifest
        if manifest.content_format == ContentFormat.MARKDOWN and not has_md:
            if has_pdf or has_pages:
                errors.append(
                    f"Submission {sid} content format doesn't match manifest (expected markdown)"
                )
        elif manifest.content_format == ContentFormat.PDF and not has_pdf:
            if has_md or has_pages:
                errors.append(
                    f"Submission {sid} content format doesn't match manifest (expected pdf)"
                )
        elif manifest.content_format == ContentFormat.IMAGES and not has_pages:
            if has_md or has_pdf:
                errors.append(
                    f"Submission {sid} content format doesn't match manifest (expected images)"
                )

    return errors


def validate_consistency(
    manifest: Manifest,
    task_core: TaskCore,
    index: SubmissionIndex,
) -> list[str]:
    """
    Validate cross-file consistency.

    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    # task_id must match
    if manifest.task_id != task_core.task_id:
        errors.append(
            f"task_id mismatch: manifest has {manifest.task_id}, task/core.json has {task_core.task_id}"
        )

    # submission_count must match index length
    if manifest.submission_count != len(index.submission_ids):
        errors.append(
            f"submission_count mismatch: manifest says {manifest.submission_count}, "
            f"_index.json has {len(index.submission_ids)} entries"
        )

    return errors


def validate_submission_consistency(
    submission_core: SubmissionCore,
    folder_name: str,
    max_grade: int,
) -> list[str]:
    """
    Validate a single submission's consistency.

    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    # submission_id must match folder name
    if submission_core.submission_id != folder_name:
        errors.append(
            f"submission_id mismatch: folder is {folder_name}, "
            f"core.json says {submission_core.submission_id}"
        )

    # grade must be in range
    if submission_core.grade > max_grade:
        errors.append(
            f"Submission {folder_name}: grade {submission_core.grade} exceeds max_grade {max_grade}"
        )

    # grade distributions must have correct length
    expected_len = max_grade + 1
    for dist_name in ["optimistic", "expected", "pessimistic"]:
        dist = getattr(submission_core.grade_distributions, dist_name)
        if len(dist) != expected_len:
            errors.append(
                f"Submission {folder_name}: {dist_name} distribution has length {len(dist)}, "
                f"expected {expected_len}"
            )

    return errors


def validate_additional_data(
    declared: list[str],
    actual: dict[str, Any],
    level: str,
    context: str = "",
) -> list[str]:
    """
    Validate additional data attributes.

    Args:
        declared: List of attribute names declared in manifest
        actual: The actual additional_data.json content
        level: "task" or "submission" for error messages
        context: Additional context (e.g., submission ID)

    Returns a list of error messages. Empty list means valid.
    """
    errors = []
    warnings = []
    prefix = f"{context}: " if context else ""

    # Check all declared attributes exist
    for attr in declared:
        if attr not in actual:
            errors.append(
                f"{prefix}{level} additional_data missing declared attribute: {attr}"
            )

    # Check no undeclared attributes exist
    declared_set = set(declared)
    for attr in actual.keys():
        if attr not in declared_set:
            errors.append(
                f"{prefix}{level} additional_data has undeclared attribute: {attr}"
            )

    # Warn about unregistered non-custom attributes
    registered = (
        REGISTERED_TASK_ATTRIBUTES
        if level == "task"
        else REGISTERED_SUBMISSION_ATTRIBUTES
    )
    for attr in declared:
        if attr not in registered and not attr.startswith("x-"):
            warnings.append(
                f"{prefix}{level} attribute '{attr}' is neither registered nor a custom (x-) attribute"
            )

    return errors  # warnings could be returned separately if needed


def validate_edf(zf: ZipFile) -> tuple[list[str], list[str]]:
    """
    Perform full validation of an EDF archive.

    Returns a tuple of (errors, warnings).
    """
    import json

    errors = []
    warnings = []

    # Parse manifest
    try:
        manifest_data = json.loads(zf.read("manifest.json"))
        manifest = Manifest.model_validate(manifest_data)
    except KeyError:
        return ["manifest.json not found in archive"], []
    except Exception as e:
        return [f"Failed to parse manifest.json: {e}"], []

    # Structural validation
    errors.extend(validate_structure(zf, manifest))
    if errors:
        return errors, warnings  # Can't continue without structure

    # Parse task core
    try:
        task_data = json.loads(zf.read("task/core.json"))
        task_core = TaskCore.model_validate(task_data)
    except Exception as e:
        errors.append(f"Failed to parse task/core.json: {e}")
        return errors, warnings

    # Parse submission index
    try:
        index_data = json.loads(zf.read("submissions/_index.json"))
        index = SubmissionIndex.model_validate(index_data)
    except Exception as e:
        errors.append(f"Failed to parse submissions/_index.json: {e}")
        return errors, warnings

    # Consistency validation
    errors.extend(validate_consistency(manifest, task_core, index))

    # Submission structure validation
    errors.extend(validate_submission_structure(zf, manifest, index.submission_ids))

    # Task additional data validation
    if manifest.additional_data.task:
        try:
            task_additional = json.loads(zf.read("task/additional_data.json"))
            errors.extend(
                validate_additional_data(
                    manifest.additional_data.task, task_additional, "task"
                )
            )
        except Exception as e:
            errors.append(f"Failed to parse task/additional_data.json: {e}")

    # Validate each submission
    for sid in index.submission_ids:
        try:
            sub_data = json.loads(zf.read(f"submissions/{sid}/core.json"))
            sub_core = SubmissionCore.model_validate(sub_data)
            errors.extend(
                validate_submission_consistency(sub_core, sid, task_core.max_grade)
            )
        except Exception as e:
            errors.append(f"Failed to parse submissions/{sid}/core.json: {e}")
            continue

        # Submission additional data
        if manifest.additional_data.submission:
            try:
                sub_additional = json.loads(
                    zf.read(f"submissions/{sid}/additional_data.json")
                )
                errors.extend(
                    validate_additional_data(
                        manifest.additional_data.submission,
                        sub_additional,
                        "submission",
                        context=f"submissions/{sid}",
                    )
                )
            except Exception as e:
                errors.append(
                    f"Failed to parse submissions/{sid}/additional_data.json: {e}"
                )

    return errors, warnings
