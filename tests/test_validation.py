"""Tests for validation module."""

import json
import pytest
from io import BytesIO
from zipfile import ZipFile

from edf.validation import (
    validate_structure,
    validate_submission_structure,
    validate_consistency,
    validate_submission_consistency,
    validate_additional_data,
    validate_edf,
    REGISTERED_TASK_ATTRIBUTES,
    REGISTERED_SUBMISSION_ATTRIBUTES,
)
from edf.models import (
    Manifest,
    TaskCore,
    SubmissionCore,
    SubmissionIndex,
    GradeDistributions,
    ContentFormat,
    AdditionalDataDeclaration,
)


def create_test_zip(files: dict[str, bytes]) -> ZipFile:
    """Create an in-memory ZipFile with given files."""
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    buffer.seek(0)
    return ZipFile(buffer, "r")


def make_manifest(**overrides) -> dict:
    """Create a valid manifest dict with optional overrides."""
    base = {
        "edf_version": "1.0.0",
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "content_hash": "sha256:" + "a" * 64,
        "created_at": 1736942400000,
        "content_format": "markdown",
        "submission_count": 1,
        "has_rubric": False,
        "has_prompt": False,
        "additional_data": {"task": [], "submission": []},
    }
    base.update(overrides)
    return base


def make_task_core(**overrides) -> dict:
    """Create a valid task/core.json dict."""
    base = {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "version": 1,
        "max_grade": 10,
    }
    base.update(overrides)
    return base


def make_submission_core(submission_id: str, grade: int = 5, max_grade: int = 10) -> dict:
    """Create a valid submission core.json dict."""
    return {
        "submission_id": submission_id,
        "grade": grade,
        "grade_distributions": {
            "optimistic": [1.0 / (max_grade + 1)] * (max_grade + 1),
            "expected": [1.0 / (max_grade + 1)] * (max_grade + 1),
            "pessimistic": [1.0 / (max_grade + 1)] * (max_grade + 1),
        },
    }


class TestValidateStructure:
    """Tests for validate_structure function."""

    def test_valid_minimal_structure(self):
        """Valid minimal structure passes."""
        manifest = Manifest.model_validate(make_manifest())
        files = {
            "manifest.json": b"{}",
            "task/core.json": b"{}",
            "submissions/_index.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_structure(zf, manifest)
        assert errors == []

    def test_missing_manifest(self):
        """Missing manifest.json is caught."""
        manifest = Manifest.model_validate(make_manifest())
        files = {
            "task/core.json": b"{}",
            "submissions/_index.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_structure(zf, manifest)
        assert any("manifest.json" in e for e in errors)

    def test_missing_task_core(self):
        """Missing task/core.json is caught."""
        manifest = Manifest.model_validate(make_manifest())
        files = {
            "manifest.json": b"{}",
            "submissions/_index.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_structure(zf, manifest)
        assert any("task/core.json" in e for e in errors)

    def test_missing_rubric_when_declared(self):
        """Missing rubric.md when has_rubric=true is caught."""
        manifest = Manifest.model_validate(make_manifest(has_rubric=True))
        files = {
            "manifest.json": b"{}",
            "task/core.json": b"{}",
            "submissions/_index.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_structure(zf, manifest)
        assert any("rubric.md" in e for e in errors)

    def test_has_rubric_with_file(self):
        """Present rubric.md when has_rubric=true passes."""
        manifest = Manifest.model_validate(make_manifest(has_rubric=True))
        files = {
            "manifest.json": b"{}",
            "task/core.json": b"{}",
            "task/rubric.md": b"# Rubric",
            "submissions/_index.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_structure(zf, manifest)
        assert not any("rubric" in e.lower() for e in errors)

    def test_missing_prompt_when_declared(self):
        """Missing prompt.md when has_prompt=true is caught."""
        manifest = Manifest.model_validate(make_manifest(has_prompt=True))
        files = {
            "manifest.json": b"{}",
            "task/core.json": b"{}",
            "submissions/_index.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_structure(zf, manifest)
        assert any("prompt.md" in e for e in errors)

    def test_task_additional_data_required(self):
        """task/additional_data.json required when declared."""
        manifest = Manifest.model_validate(
            make_manifest(additional_data={"task": ["school_id"], "submission": []})
        )
        files = {
            "manifest.json": b"{}",
            "task/core.json": b"{}",
            "submissions/_index.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_structure(zf, manifest)
        assert any("additional_data.json" in e for e in errors)

    def test_unexpected_additional_data(self):
        """task/additional_data.json without declaration is error."""
        manifest = Manifest.model_validate(make_manifest())
        files = {
            "manifest.json": b"{}",
            "task/core.json": b"{}",
            "task/additional_data.json": b"{}",
            "submissions/_index.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_structure(zf, manifest)
        assert any("exists but no" in e for e in errors)


class TestValidateSubmissionStructure:
    """Tests for validate_submission_structure function."""

    def test_valid_submission_structure(self):
        """Valid submission structure passes."""
        manifest = Manifest.model_validate(make_manifest())
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/content.md": b"content",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert errors == []

    def test_missing_submission_core(self):
        """Missing core.json in submission is caught."""
        manifest = Manifest.model_validate(make_manifest())
        files = {
            "submissions/test_sub/content.md": b"content",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("core.json" in e for e in errors)

    def test_submission_additional_data_required(self):
        """Missing additional_data.json when declared is caught."""
        manifest = Manifest.model_validate(
            make_manifest(additional_data={"task": [], "submission": ["student_name"]})
        )
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/content.md": b"content",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("additional_data.json" in e for e in errors)

    def test_submission_unexpected_additional_data(self):
        """Unexpected additional_data.json is caught."""
        manifest = Manifest.model_validate(make_manifest())
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/content.md": b"content",
            "submissions/test_sub/additional_data.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("exists but no" in e for e in errors)

    def test_submission_no_content(self):
        """Submission with no content is caught."""
        manifest = Manifest.model_validate(make_manifest())
        files = {
            "submissions/test_sub/core.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("no content" in e for e in errors)

    def test_submission_no_content_pdf_format(self):
        """Submission with no content in PDF format is caught."""
        manifest = Manifest.model_validate(make_manifest(content_format="pdf"))
        files = {
            "submissions/test_sub/core.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("no content" in e for e in errors)

    def test_submission_no_content_images_format(self):
        """Submission with no content in images format is caught."""
        manifest = Manifest.model_validate(make_manifest(content_format="images"))
        files = {
            "submissions/test_sub/core.json": b"{}",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("no content" in e for e in errors)

    def test_submission_multiple_content_types(self):
        """Submission with multiple content types is caught."""
        manifest = Manifest.model_validate(make_manifest())
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/content.md": b"markdown",
            "submissions/test_sub/content.pdf": b"pdf",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("multiple content types" in e for e in errors)

    def test_submission_format_mismatch_expected_markdown_got_pdf(self):
        """Content format mismatch: expected markdown, got pdf."""
        manifest = Manifest.model_validate(make_manifest(content_format="markdown"))
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/content.pdf": b"pdf",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("expected markdown" in e for e in errors)

    def test_submission_format_mismatch_expected_markdown_got_images(self):
        """Content format mismatch: expected markdown, got images."""
        manifest = Manifest.model_validate(make_manifest(content_format="markdown"))
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/pages/0.jpg": b"jpg",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("expected markdown" in e for e in errors)

    def test_submission_format_mismatch_expected_pdf_got_markdown(self):
        """Content format mismatch: expected pdf, got markdown."""
        manifest = Manifest.model_validate(make_manifest(content_format="pdf"))
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/content.md": b"markdown",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("expected pdf" in e for e in errors)

    def test_submission_format_mismatch_expected_pdf_got_images(self):
        """Content format mismatch: expected pdf, got images."""
        manifest = Manifest.model_validate(make_manifest(content_format="pdf"))
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/pages/0.jpg": b"jpg",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("expected pdf" in e for e in errors)

    def test_submission_format_mismatch_expected_images_got_markdown(self):
        """Content format mismatch: expected images, got markdown."""
        manifest = Manifest.model_validate(make_manifest(content_format="images"))
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/content.md": b"markdown",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("expected images" in e for e in errors)

    def test_submission_format_mismatch_expected_images_got_pdf(self):
        """Content format mismatch: expected images, got pdf."""
        manifest = Manifest.model_validate(make_manifest(content_format="images"))
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/content.pdf": b"pdf",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert any("expected images" in e for e in errors)

    def test_valid_pdf_submission(self):
        """Valid PDF submission passes."""
        manifest = Manifest.model_validate(make_manifest(content_format="pdf"))
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/content.pdf": b"pdf content",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert errors == []

    def test_valid_images_submission(self):
        """Valid images submission passes."""
        manifest = Manifest.model_validate(make_manifest(content_format="images"))
        files = {
            "submissions/test_sub/core.json": b"{}",
            "submissions/test_sub/pages/0.jpg": b"jpg content",
        }
        zf = create_test_zip(files)
        errors = validate_submission_structure(zf, manifest, ["test_sub"])
        assert errors == []


class TestValidateConsistency:
    """Tests for validate_consistency function."""

    def test_matching_ids(self):
        """Matching task_id and submission_count passes."""
        manifest = Manifest.model_validate(make_manifest(submission_count=2))
        task = TaskCore.model_validate(make_task_core())
        index = SubmissionIndex(submission_ids=["a", "b"])
        errors = validate_consistency(manifest, task, index)
        assert errors == []

    def test_mismatched_task_id(self):
        """Mismatched task_id is caught."""
        manifest = Manifest.model_validate(make_manifest())
        task = TaskCore.model_validate(
            make_task_core(task_id="660e8400-e29b-41d4-a716-446655440000")
        )
        index = SubmissionIndex(submission_ids=["a"])
        errors = validate_consistency(manifest, task, index)
        assert any("task_id mismatch" in e for e in errors)

    def test_mismatched_submission_count(self):
        """Mismatched submission_count is caught."""
        manifest = Manifest.model_validate(make_manifest(submission_count=3))
        task = TaskCore.model_validate(make_task_core())
        index = SubmissionIndex(submission_ids=["a", "b"])
        errors = validate_consistency(manifest, task, index)
        assert any("submission_count mismatch" in e for e in errors)


class TestValidateSubmissionConsistency:
    """Tests for validate_submission_consistency function."""

    def test_valid_submission(self):
        """Valid submission passes."""
        core = SubmissionCore.model_validate(make_submission_core("test", grade=5))
        errors = validate_submission_consistency(core, "test", max_grade=10)
        assert errors == []

    def test_id_mismatch(self):
        """Mismatched submission_id is caught."""
        core = SubmissionCore.model_validate(make_submission_core("wrong_id", grade=5))
        errors = validate_submission_consistency(core, "expected_id", max_grade=10)
        assert any("mismatch" in e for e in errors)

    def test_grade_exceeds_max(self):
        """Grade exceeding max_grade is caught."""
        core = SubmissionCore.model_validate(make_submission_core("test", grade=15))
        errors = validate_submission_consistency(core, "test", max_grade=10)
        assert any("exceeds" in e for e in errors)

    def test_wrong_distribution_length(self):
        """Wrong distribution length is caught."""
        core_dict = make_submission_core("test", grade=5, max_grade=5)
        core = SubmissionCore.model_validate(core_dict)
        # Distribution has length 6 (for max_grade=5), but we check against max_grade=10
        errors = validate_submission_consistency(core, "test", max_grade=10)
        assert any("length" in e for e in errors)


class TestValidateAdditionalData:
    """Tests for validate_additional_data function."""

    def test_all_declared_present(self):
        """All declared attributes present passes."""
        declared = ["school_id", "subject_code"]
        actual = {"school_id": "TEST", "subject_code": "CS101"}
        errors = validate_additional_data(declared, actual, "task")
        assert errors == []

    def test_missing_declared(self):
        """Missing declared attribute is error."""
        declared = ["school_id", "subject_code"]
        actual = {"school_id": "TEST"}
        errors = validate_additional_data(declared, actual, "task")
        assert any("missing declared" in e for e in errors)

    def test_undeclared_attribute(self):
        """Undeclared attribute is error."""
        declared = ["school_id"]
        actual = {"school_id": "TEST", "extra": "value"}
        errors = validate_additional_data(declared, actual, "task")
        assert any("undeclared" in e for e in errors)

    def test_null_values_allowed(self):
        """Null values for declared attributes are allowed."""
        declared = ["school_id"]
        actual = {"school_id": None}
        errors = validate_additional_data(declared, actual, "task")
        assert errors == []


class TestValidateEDF:
    """Tests for full validate_edf function."""

    def test_valid_edf(self):
        """Valid EDF passes."""
        manifest = make_manifest()
        task_core = make_task_core()
        sub_core = make_submission_core("test_sub")
        index = {"submission_ids": ["test_sub"]}

        files = {
            "manifest.json": json.dumps(manifest).encode(),
            "task/core.json": json.dumps(task_core).encode(),
            "submissions/_index.json": json.dumps(index).encode(),
            "submissions/test_sub/core.json": json.dumps(sub_core).encode(),
            "submissions/test_sub/content.md": b"Test content",
        }
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert errors == []

    def test_missing_manifest(self):
        """Missing manifest is caught."""
        files = {"task/core.json": b"{}"}
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert any("manifest.json" in e for e in errors)

    def test_invalid_manifest_json(self):
        """Invalid manifest JSON is caught."""
        files = {"manifest.json": b"not valid json"}
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert any("parse" in e.lower() or "manifest" in e.lower() for e in errors)

    def test_structure_errors_stop_early(self):
        """Structural errors stop validation early."""
        manifest = make_manifest()
        # Missing task/core.json - should fail structure check
        files = {
            "manifest.json": json.dumps(manifest).encode(),
            "submissions/_index.json": b"{}",
        }
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert any("task/core.json" in e for e in errors)

    def test_invalid_task_core_json(self):
        """Invalid task/core.json is caught."""
        manifest = make_manifest()
        files = {
            "manifest.json": json.dumps(manifest).encode(),
            "task/core.json": b"not valid json",
            "submissions/_index.json": b"{}",
        }
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert any("task/core.json" in e for e in errors)

    def test_invalid_index_json(self):
        """Invalid submissions/_index.json is caught."""
        manifest = make_manifest()
        task_core = make_task_core()
        files = {
            "manifest.json": json.dumps(manifest).encode(),
            "task/core.json": json.dumps(task_core).encode(),
            "submissions/_index.json": b"not valid json",
        }
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert any("_index.json" in e for e in errors)

    def test_invalid_task_additional_data_json(self):
        """Invalid task/additional_data.json is caught."""
        manifest = make_manifest(additional_data={"task": ["school_id"], "submission": []})
        task_core = make_task_core()
        index = {"submission_ids": []}
        files = {
            "manifest.json": json.dumps(manifest).encode(),
            "task/core.json": json.dumps(task_core).encode(),
            "task/additional_data.json": b"not valid json",
            "submissions/_index.json": json.dumps(index).encode(),
        }
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert any("additional_data.json" in e for e in errors)

    def test_invalid_submission_core_json(self):
        """Invalid submission core.json is caught."""
        manifest = make_manifest()
        task_core = make_task_core()
        index = {"submission_ids": ["test_sub"]}
        files = {
            "manifest.json": json.dumps(manifest).encode(),
            "task/core.json": json.dumps(task_core).encode(),
            "submissions/_index.json": json.dumps(index).encode(),
            "submissions/test_sub/core.json": b"not valid json",
            "submissions/test_sub/content.md": b"Test content",
        }
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert any("test_sub/core.json" in e for e in errors)

    def test_invalid_submission_additional_data_json(self):
        """Invalid submission additional_data.json is caught."""
        manifest = make_manifest(additional_data={"task": [], "submission": ["student_name"]})
        task_core = make_task_core()
        sub_core = make_submission_core("test_sub")
        index = {"submission_ids": ["test_sub"]}
        files = {
            "manifest.json": json.dumps(manifest).encode(),
            "task/core.json": json.dumps(task_core).encode(),
            "submissions/_index.json": json.dumps(index).encode(),
            "submissions/test_sub/core.json": json.dumps(sub_core).encode(),
            "submissions/test_sub/additional_data.json": b"not valid json",
            "submissions/test_sub/content.md": b"Test content",
        }
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert any("additional_data.json" in e for e in errors)

    def test_valid_edf_with_task_additional_data(self):
        """Valid EDF with task additional data passes."""
        manifest = make_manifest(additional_data={"task": ["school_id"], "submission": []})
        task_core = make_task_core()
        sub_core = make_submission_core("test_sub")
        index = {"submission_ids": ["test_sub"]}
        files = {
            "manifest.json": json.dumps(manifest).encode(),
            "task/core.json": json.dumps(task_core).encode(),
            "task/additional_data.json": json.dumps({"school_id": "TEST"}).encode(),
            "submissions/_index.json": json.dumps(index).encode(),
            "submissions/test_sub/core.json": json.dumps(sub_core).encode(),
            "submissions/test_sub/content.md": b"Test content",
        }
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert errors == []

    def test_valid_edf_with_submission_additional_data(self):
        """Valid EDF with submission additional data passes."""
        manifest = make_manifest(additional_data={"task": [], "submission": ["student_name"]})
        task_core = make_task_core()
        sub_core = make_submission_core("test_sub")
        index = {"submission_ids": ["test_sub"]}
        files = {
            "manifest.json": json.dumps(manifest).encode(),
            "task/core.json": json.dumps(task_core).encode(),
            "submissions/_index.json": json.dumps(index).encode(),
            "submissions/test_sub/core.json": json.dumps(sub_core).encode(),
            "submissions/test_sub/additional_data.json": json.dumps({"student_name": "Test"}).encode(),
            "submissions/test_sub/content.md": b"Test content",
        }
        zf = create_test_zip(files)
        errors, warnings = validate_edf(zf)
        assert errors == []


class TestRegisteredAttributes:
    """Tests for registered attribute sets."""

    def test_task_attributes(self):
        """Check expected task attributes are registered."""
        assert "school_id" in REGISTERED_TASK_ATTRIBUTES
        assert "subject_code" in REGISTERED_TASK_ATTRIBUTES
        assert "academic_year" in REGISTERED_TASK_ATTRIBUTES

    def test_submission_attributes(self):
        """Check expected submission attributes are registered."""
        assert "student_name" in REGISTERED_SUBMISSION_ATTRIBUTES
        assert "student_id" in REGISTERED_SUBMISSION_ATTRIBUTES
        assert "grader_id" in REGISTERED_SUBMISSION_ATTRIBUTES
        assert "marker_feedback" in REGISTERED_SUBMISSION_ATTRIBUTES
        assert "llm_context" in REGISTERED_SUBMISSION_ATTRIBUTES
