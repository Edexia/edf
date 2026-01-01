"""Tests for the core EDF class."""

import math
import pytest
import uuid
from pathlib import Path

from edf import EDF, EDF_VERSION, ContentFormat, EPHEMERAL_TASK_ID, EPHEMERAL_VERSION
from edf.exceptions import EDFError, EDFValidationError


def make_distribution(peak: int, max_grade: int, sigma: float = 2.0) -> list[float]:
    """Generate a Gaussian distribution for testing."""
    dist = [math.exp(-((i - peak) ** 2) / (2 * sigma ** 2)) for i in range(max_grade + 1)]
    total = sum(dist)
    return [p / total for p in dist]


class TestEDFCreation:
    """Tests for creating new EDF instances."""

    def test_create_minimal(self):
        """Create EDF with only required parameter."""
        edf = EDF(max_grade=10)
        assert edf.max_grade == 10
        assert edf.version == 1
        assert edf.edf_version == EDF_VERSION
        assert edf.rubric is None
        assert edf.prompt is None
        assert len(edf.submissions) == 0

    def test_create_with_task_id(self):
        """Create EDF with explicit task_id."""
        task_id = "550e8400-e29b-41d4-a716-446655440000"
        edf = EDF(max_grade=10, task_id=task_id)
        assert edf.task_id == task_id

    def test_create_auto_generates_task_id(self):
        """Task ID is auto-generated as valid UUID."""
        edf = EDF(max_grade=10)
        # Should be valid UUID v4
        parsed = uuid.UUID(edf.task_id)
        assert parsed.version == 4

    def test_create_with_version(self):
        """Create EDF with explicit version."""
        edf = EDF(max_grade=10, version=5)
        assert edf.version == 5

    def test_create_with_edf_version(self):
        """Create EDF with explicit edf_version."""
        edf = EDF(max_grade=10, edf_version="2.0.0")
        assert edf.edf_version == "2.0.0"


class TestEDFProperties:
    """Tests for EDF property getters and setters."""

    def test_rubric_setter(self):
        """Set and get rubric."""
        edf = EDF(max_grade=10)
        edf.rubric = "# Test Rubric"
        assert edf.rubric == "# Test Rubric"

    def test_rubric_set_none(self):
        """Set rubric to None."""
        edf = EDF(max_grade=10)
        edf.rubric = "# Test"
        edf.rubric = None
        assert edf.rubric is None

    def test_prompt_setter(self):
        """Set and get prompt."""
        edf = EDF(max_grade=10)
        edf.prompt = "# Test Prompt"
        assert edf.prompt == "# Test Prompt"

    def test_version_setter(self):
        """Set version property."""
        edf = EDF(max_grade=10)
        edf.version = 3
        assert edf.version == 3

    def test_version_setter_invalid(self):
        """Version must be >= 1."""
        edf = EDF(max_grade=10)
        with pytest.raises(ValueError, match="version must be >= 1"):
            edf.version = 0

    def test_task_data_readonly(self):
        """task_data property returns dict but modifications need set_task_data."""
        edf = EDF(max_grade=10)
        edf.set_task_data(foo="bar")
        assert edf.task_data == {"foo": "bar"}

    def test_content_format_none_when_empty(self):
        """content_format is None when no submissions."""
        edf = EDF(max_grade=10)
        assert edf.content_format is None

    def test_content_format_from_submission(self, simple_edf):
        """content_format is detected from submissions."""
        assert simple_edf.content_format == ContentFormat.MARKDOWN

    def test_created_at_none_before_save(self):
        """created_at is None before save."""
        edf = EDF(max_grade=10)
        assert edf.created_at is None

    def test_content_hash_none_before_save(self):
        """content_hash is None before save."""
        edf = EDF(max_grade=10)
        assert edf.content_hash is None


class TestEDFTaskData:
    """Tests for task-level additional data."""

    def test_set_task_data(self):
        """Set task data with kwargs."""
        edf = EDF(max_grade=10)
        edf.set_task_data(school_id="TEST-001", subject_code="MATH-101")
        assert edf.task_data["school_id"] == "TEST-001"
        assert edf.task_data["subject_code"] == "MATH-101"

    def test_set_task_data_chaining(self):
        """set_task_data returns self for chaining."""
        edf = EDF(max_grade=10)
        result = edf.set_task_data(foo="bar")
        assert result is edf

    def test_set_task_data_merge(self):
        """Multiple set_task_data calls merge data."""
        edf = EDF(max_grade=10)
        edf.set_task_data(a="1")
        edf.set_task_data(b="2")
        assert edf.task_data == {"a": "1", "b": "2"}

    def test_set_task_data_overwrite(self):
        """set_task_data overwrites existing keys."""
        edf = EDF(max_grade=10)
        edf.set_task_data(a="1")
        edf.set_task_data(a="2")
        assert edf.task_data["a"] == "2"


class TestEDFSubmissions:
    """Tests for adding and managing submissions."""

    def test_add_submission_markdown(self, uniform_distribution):
        """Add markdown submission."""
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content="Markdown content",
        )
        assert len(edf.submissions) == 1
        assert edf.submissions[0].id == "test"
        assert edf.submissions[0].grade == 5
        assert edf.content_format == ContentFormat.MARKDOWN

    def test_add_submission_pdf(self, uniform_distribution):
        """Add PDF submission."""
        edf = EDF(max_grade=10)
        pdf_bytes = b"%PDF-1.4 fake pdf content"
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content=pdf_bytes,
        )
        assert edf.content_format == ContentFormat.PDF
        assert edf.submissions[0].get_pdf() == pdf_bytes

    def test_add_submission_images(self, uniform_distribution):
        """Add image submission."""
        edf = EDF(max_grade=10)
        images = [b"fake jpg 1", b"fake jpg 2"]
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content=images,
        )
        assert edf.content_format == ContentFormat.IMAGES
        assert edf.submissions[0].get_images() == images

    def test_add_submission_with_additional_data(self, uniform_distribution):
        """Add submission with additional metadata."""
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content="content",
            student_name="Test Student",
            student_id="12345",
        )
        sub = edf.submissions[0]
        assert sub.additional["student_name"] == "Test Student"
        assert sub.additional["student_id"] == "12345"

    def test_add_submission_chaining(self, uniform_distribution):
        """add_submission returns self for chaining."""
        edf = EDF(max_grade=10)
        result = edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content="content",
        )
        assert result is edf

    def test_add_submission_invalid_id_empty(self, uniform_distribution):
        """Reject empty submission_id."""
        edf = EDF(max_grade=10)
        with pytest.raises(ValueError, match="submission_id must be alphanumeric"):
            edf.add_submission(
                submission_id="",
                grade=5,
                optimistic=uniform_distribution,
                expected=uniform_distribution,
                pessimistic=uniform_distribution,
                content="content",
            )

    def test_add_submission_invalid_id_special_chars(self, uniform_distribution):
        """Reject submission_id with special characters."""
        edf = EDF(max_grade=10)
        with pytest.raises(ValueError, match="submission_id must be alphanumeric"):
            edf.add_submission(
                submission_id="test-student",
                grade=5,
                optimistic=uniform_distribution,
                expected=uniform_distribution,
                pessimistic=uniform_distribution,
                content="content",
            )

    def test_add_submission_duplicate_id(self, uniform_distribution):
        """Reject duplicate submission_id."""
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content="content",
        )
        with pytest.raises(ValueError, match="already exists"):
            edf.add_submission(
                submission_id="test",
                grade=5,
                optimistic=uniform_distribution,
                expected=uniform_distribution,
                pessimistic=uniform_distribution,
                content="more content",
            )

    def test_add_submission_grade_out_of_range(self, uniform_distribution):
        """Reject grade outside [0, max_grade]."""
        edf = EDF(max_grade=10)
        with pytest.raises(ValueError, match="grade must be in"):
            edf.add_submission(
                submission_id="test",
                grade=11,
                optimistic=uniform_distribution,
                expected=uniform_distribution,
                pessimistic=uniform_distribution,
                content="content",
            )

    def test_add_submission_grade_negative(self, uniform_distribution):
        """Reject negative grade."""
        edf = EDF(max_grade=10)
        with pytest.raises(ValueError, match="grade must be in"):
            edf.add_submission(
                submission_id="test",
                grade=-1,
                optimistic=uniform_distribution,
                expected=uniform_distribution,
                pessimistic=uniform_distribution,
                content="content",
            )

    def test_add_submission_mixed_formats(self, uniform_distribution):
        """Reject mixed content formats."""
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="markdown_sub",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content="markdown",
        )
        with pytest.raises(ValueError, match="Content format mismatch"):
            edf.add_submission(
                submission_id="pdf_sub",
                grade=5,
                optimistic=uniform_distribution,
                expected=uniform_distribution,
                pessimistic=uniform_distribution,
                content=b"pdf bytes",
            )

    def test_add_submission_invalid_content_type(self, uniform_distribution):
        """Reject invalid content types (not str, bytes, or list[bytes])."""
        edf = EDF(max_grade=10)
        with pytest.raises(ValueError, match="content must be str"):
            edf.add_submission(
                submission_id="test",
                grade=5,
                optimistic=uniform_distribution,
                expected=uniform_distribution,
                pessimistic=uniform_distribution,
                content=12345,  # Invalid content type
            )

    def test_get_submission(self, simple_edf):
        """Get submission by ID."""
        sub = simple_edf.get_submission("test_student")
        assert sub.id == "test_student"
        assert sub.grade == 7

    def test_get_submission_not_found(self, simple_edf):
        """get_submission raises KeyError for unknown ID."""
        with pytest.raises(KeyError):
            simple_edf.get_submission("nonexistent")

    def test_remove_submission(self, uniform_distribution):
        """Remove a submission."""
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content="content",
        )
        assert len(edf.submissions) == 1
        edf.remove_submission("test")
        assert len(edf.submissions) == 0

    def test_remove_submission_not_found(self, simple_edf):
        """remove_submission raises KeyError for unknown ID."""
        with pytest.raises(KeyError):
            simple_edf.remove_submission("nonexistent")

    def test_submission_ids_property(self, full_edf):
        """submission_ids returns list of IDs."""
        ids = full_edf.submission_ids
        assert "student_alice" in ids
        assert "student_bob" in ids
        assert "student_carol" in ids
        assert len(ids) == 3


class TestEDFSaveAndOpen:
    """Tests for saving and opening EDF files."""

    def test_save_and_open(self, simple_edf, tmp_edf_path):
        """Save and reopen an EDF file."""
        simple_edf.save(tmp_edf_path)
        assert tmp_edf_path.exists()

        with EDF.open(tmp_edf_path) as loaded:
            assert loaded.max_grade == simple_edf.max_grade
            assert loaded.task_id == simple_edf.task_id
            assert len(loaded.submissions) == 1

    def test_save_sets_created_at(self, simple_edf, tmp_edf_path):
        """Saving sets created_at timestamp."""
        assert simple_edf.created_at is None
        simple_edf.save(tmp_edf_path)
        assert simple_edf.created_at is not None
        assert simple_edf.created_at > 0

    def test_save_sets_content_hash(self, simple_edf, tmp_edf_path):
        """Saving sets content_hash."""
        assert simple_edf.content_hash is None
        simple_edf.save(tmp_edf_path)
        assert simple_edf.content_hash is not None
        assert simple_edf.content_hash.startswith("sha256:")

    def test_save_no_submissions_fails(self, tmp_edf_path):
        """Cannot save EDF with no submissions."""
        edf = EDF(max_grade=10)
        with pytest.raises(ValueError, match="no submissions"):
            edf.save(tmp_edf_path)

    def test_save_full_edf(self, full_edf, tmp_edf_path):
        """Save and reload full EDF with all features."""
        full_edf.save(tmp_edf_path)

        with EDF.open(tmp_edf_path) as loaded:
            assert loaded.rubric == full_edf.rubric
            assert loaded.prompt == full_edf.prompt
            assert loaded.task_data == full_edf.task_data
            assert len(loaded.submissions) == 3

            sub = loaded.get_submission("student_alice")
            assert sub.grade == 18
            assert sub.additional["student_name"] == "Alice"

    def test_open_with_validation(self, saved_edf):
        """Open with validation enabled."""
        with EDF.open(saved_edf, validate=True) as edf:
            assert len(edf.submissions) == 3

    def test_open_without_validation(self, saved_edf):
        """Open with validation disabled."""
        with EDF.open(saved_edf, validate=False) as edf:
            assert len(edf.submissions) == 3

    def test_context_manager(self, saved_edf):
        """EDF works as context manager."""
        with EDF.open(saved_edf) as edf:
            assert edf.max_grade == 20
        # After exiting, the file should be closed
        # (no easy way to test this, but at least it shouldn't raise)

    def test_content_preserved_after_reload(self, simple_edf, tmp_edf_path):
        """Submission content is preserved through save/load cycle."""
        simple_edf.save(tmp_edf_path)

        with EDF.open(tmp_edf_path) as loaded:
            sub = loaded.get_submission("test_student")
            assert sub.get_markdown() == "Test answer content"

    def test_edf_version_preserved(self, tmp_edf_path):
        """EDF version is preserved through save/load."""
        edf = EDF(max_grade=10, edf_version="1.0.0")
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=[1/11]*11,
            expected=[1/11]*11,
            pessimistic=[1/11]*11,
            content="test",
        )
        edf.save(tmp_edf_path)

        with EDF.open(tmp_edf_path) as loaded:
            assert loaded.edf_version == "1.0.0"


class TestEDFClose:
    """Tests for EDF close behavior."""

    def test_close_on_new_edf(self):
        """Closing a newly created EDF (not opened from file) works."""
        edf = EDF(max_grade=10)
        edf.close()  # Should not raise
        edf.close()  # Should be safe to call multiple times

    def test_close_after_open(self, saved_edf):
        """Closing an opened EDF works."""
        edf = EDF.open(saved_edf)
        edf.close()
        edf.close()  # Should be safe to call multiple times


class TestEDFModification:
    """Tests for modifying an opened EDF."""

    def test_add_submission_to_opened(self, saved_edf, tmp_path):
        """Add submission to opened EDF and save."""
        output = tmp_path / "modified.edf"

        with EDF.open(saved_edf) as edf:
            edf.add_submission(
                submission_id="student_new",
                grade=10,
                optimistic=make_distribution(11, 20),
                expected=make_distribution(10, 20),
                pessimistic=make_distribution(9, 20),
                content="New student answer",
                student_name="New Student",
            )
            edf.save(output)

        with EDF.open(output) as reloaded:
            assert len(reloaded.submissions) == 4
            assert "student_new" in reloaded.submission_ids

    def test_modify_rubric_and_save(self, saved_edf, tmp_path):
        """Modify rubric and save."""
        output = tmp_path / "modified.edf"

        with EDF.open(saved_edf) as edf:
            edf.rubric = "# Updated Rubric"
            edf.save(output)

        with EDF.open(output) as reloaded:
            assert reloaded.rubric == "# Updated Rubric"


class TestEDFFromDirectory:
    """Tests for loading EDFs from unzipped directories."""

    def test_from_directory_requires_flag(self, unzipped_edf_dir):
        """from_directory requires dangerously_load_unzipped_edf=True."""
        with pytest.raises(ValueError, match="dangerously_load_unzipped_edf"):
            EDF.from_directory(unzipped_edf_dir)

    def test_from_directory_loads_markdown_edf(self, unzipped_edf_dir):
        """Load a markdown EDF from directory."""
        edf = EDF.from_directory(unzipped_edf_dir, dangerously_load_unzipped_edf=True)
        assert edf.is_ephemeral
        assert edf.task_id == EPHEMERAL_TASK_ID
        assert edf.version == EPHEMERAL_VERSION
        assert len(edf.submissions) == 3
        assert edf.content_format == ContentFormat.MARKDOWN

    def test_from_directory_loads_pdf_edf(self, unzipped_pdf_edf_dir):
        """Load a PDF EDF from directory."""
        edf = EDF.from_directory(unzipped_pdf_edf_dir, dangerously_load_unzipped_edf=True)
        assert edf.is_ephemeral
        assert edf.content_format == ContentFormat.PDF
        sub = edf.get_submission("sub1")
        assert sub.get_pdf() == b"%PDF-1.4 fake pdf"

    def test_from_directory_loads_images_edf(self, unzipped_images_edf_dir):
        """Load an images EDF from directory."""
        edf = EDF.from_directory(unzipped_images_edf_dir, dangerously_load_unzipped_edf=True)
        assert edf.is_ephemeral
        assert edf.content_format == ContentFormat.IMAGES
        sub = edf.get_submission("sub1")
        images = sub.get_images()
        assert len(images) == 2
        assert images[0] == b"fake jpg 0"
        assert images[1] == b"fake jpg 1"

    def test_from_directory_loads_rubric_and_prompt(self, unzipped_edf_dir):
        """Load rubric and prompt from directory."""
        edf = EDF.from_directory(unzipped_edf_dir, dangerously_load_unzipped_edf=True)
        assert edf.rubric is not None
        assert "Criterion 1" in edf.rubric
        assert edf.prompt is not None
        assert "Assignment" in edf.prompt

    def test_from_directory_loads_task_data(self, unzipped_edf_dir):
        """Load task additional data from directory."""
        edf = EDF.from_directory(unzipped_edf_dir, dangerously_load_unzipped_edf=True)
        assert edf.task_data["school_id"] == "TEST-001"
        assert edf.task_data["subject_code"] == "TEST-101"

    def test_from_directory_loads_submission_data(self, unzipped_edf_dir):
        """Load submission additional data from directory."""
        edf = EDF.from_directory(unzipped_edf_dir, dangerously_load_unzipped_edf=True)
        sub = edf.get_submission("student_alice")
        assert sub.additional["student_name"] == "Alice"

    def test_from_directory_not_a_directory(self, saved_edf):
        """from_directory raises error for file path."""
        with pytest.raises(EDFError, match="Not a directory"):
            EDF.from_directory(saved_edf, dangerously_load_unzipped_edf=True)

    def test_from_directory_missing_manifest(self, tmp_path):
        """from_directory raises error for missing manifest."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(EDFError, match="Missing manifest.json"):
            EDF.from_directory(empty_dir, dangerously_load_unzipped_edf=True)

    def test_from_directory_missing_task_core(self, tmp_path):
        """from_directory raises error for missing task/core.json."""
        import json
        edf_dir = tmp_path / "edf"
        edf_dir.mkdir()
        manifest = {
            "edf_version": "1.0.0",
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "content_hash": "sha256:" + "a" * 64,
            "created_at": 1700000000000,
            "content_format": "markdown",
            "submission_count": 0,
            "has_rubric": False,
            "has_prompt": False,
            "additional_data": {"task": [], "submission": []},
        }
        (edf_dir / "manifest.json").write_text(json.dumps(manifest))
        with pytest.raises(EDFError, match="Missing task/core.json"):
            EDF.from_directory(edf_dir, dangerously_load_unzipped_edf=True)

    def test_from_directory_missing_submissions_index(self, tmp_path):
        """from_directory raises error for missing submissions/_index.json."""
        import json
        edf_dir = tmp_path / "edf"
        edf_dir.mkdir()
        manifest = {
            "edf_version": "1.0.0",
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "content_hash": "sha256:" + "a" * 64,
            "created_at": 1700000000000,
            "content_format": "markdown",
            "submission_count": 0,
            "has_rubric": False,
            "has_prompt": False,
            "additional_data": {"task": [], "submission": []},
        }
        (edf_dir / "manifest.json").write_text(json.dumps(manifest))
        task_dir = edf_dir / "task"
        task_dir.mkdir()
        (task_dir / "core.json").write_text(json.dumps({
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "version": 1,
            "max_grade": 10,
        }))
        with pytest.raises(EDFError, match="Missing submissions/_index.json"):
            EDF.from_directory(edf_dir, dangerously_load_unzipped_edf=True)

    def test_from_directory_missing_submission_core(self, tmp_path):
        """from_directory raises error for missing submission core.json."""
        import json
        edf_dir = tmp_path / "edf"
        edf_dir.mkdir()
        manifest = {
            "edf_version": "1.0.0",
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "content_hash": "sha256:" + "a" * 64,
            "created_at": 1700000000000,
            "content_format": "markdown",
            "submission_count": 1,
            "has_rubric": False,
            "has_prompt": False,
            "additional_data": {"task": [], "submission": []},
        }
        (edf_dir / "manifest.json").write_text(json.dumps(manifest))
        task_dir = edf_dir / "task"
        task_dir.mkdir()
        (task_dir / "core.json").write_text(json.dumps({
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "version": 1,
            "max_grade": 10,
        }))
        submissions_dir = edf_dir / "submissions"
        submissions_dir.mkdir()
        (submissions_dir / "_index.json").write_text(json.dumps({"submission_ids": ["sub1"]}))
        (submissions_dir / "sub1").mkdir()
        with pytest.raises(EDFError, match="Missing submissions/sub1/core.json"):
            EDF.from_directory(edf_dir, dangerously_load_unzipped_edf=True)

    def test_ephemeral_edf_has_no_created_at(self, unzipped_edf_dir):
        """Ephemeral EDFs have created_at=None."""
        edf = EDF.from_directory(unzipped_edf_dir, dangerously_load_unzipped_edf=True)
        assert edf.created_at is None

    def test_ephemeral_edf_has_no_content_hash(self, unzipped_edf_dir):
        """Ephemeral EDFs have content_hash=None."""
        edf = EDF.from_directory(unzipped_edf_dir, dangerously_load_unzipped_edf=True)
        assert edf.content_hash is None

    def test_from_directory_handles_missing_declared_files(self, unzipped_edf_missing_files):
        """from_directory gracefully handles missing rubric/prompt/additional_data files."""
        # The manifest declares rubric, prompt, and additional_data but they don't exist
        edf = EDF.from_directory(unzipped_edf_missing_files, dangerously_load_unzipped_edf=True)

        # These should be None/empty since the files don't exist
        assert edf.rubric is None
        assert edf.prompt is None
        assert edf.task_data == {}
        sub = edf.get_submission("sub1")
        assert sub.additional == {}


class TestEDFEphemeralSave:
    """Tests for saving ephemeral EDFs."""

    def test_save_ephemeral_generates_new_uuid(self, unzipped_edf_dir, tmp_path, capsys):
        """Saving an ephemeral EDF generates a new task_id."""
        edf = EDF.from_directory(unzipped_edf_dir, dangerously_load_unzipped_edf=True)
        assert edf.is_ephemeral

        output = tmp_path / "saved.edf"
        edf.save(output)

        # Should no longer be ephemeral after save
        assert not edf.is_ephemeral
        assert edf.task_id != EPHEMERAL_TASK_ID
        assert edf.version == 1

        # Should have printed warning
        captured = capsys.readouterr()
        assert "Warning: Saving ephemeral EDF" in captured.err
        assert "Generated new task_id" in captured.err

    def test_saved_ephemeral_can_be_reopened(self, unzipped_edf_dir, tmp_path):
        """A saved ephemeral EDF can be reopened normally."""
        edf = EDF.from_directory(unzipped_edf_dir, dangerously_load_unzipped_edf=True)
        output = tmp_path / "saved.edf"
        edf.save(output)
        saved_task_id = edf.task_id

        with EDF.open(output, validate=True) as reloaded:
            assert reloaded.task_id == saved_task_id
            assert reloaded.version == 1
            assert len(reloaded.submissions) == 3


class TestIsEphemeralProperty:
    """Tests for the is_ephemeral property."""

    def test_new_edf_not_ephemeral(self):
        """Newly created EDF is not ephemeral."""
        edf = EDF(max_grade=10)
        assert not edf.is_ephemeral

    def test_opened_edf_not_ephemeral(self, saved_edf):
        """EDF opened from file is not ephemeral."""
        with EDF.open(saved_edf) as edf:
            assert not edf.is_ephemeral

    def test_ephemeral_edf_from_directory(self, unzipped_edf_dir):
        """EDF loaded from directory is ephemeral."""
        edf = EDF.from_directory(unzipped_edf_dir, dangerously_load_unzipped_edf=True)
        assert edf.is_ephemeral


class TestOpenDirectoryError:
    """Tests for helpful error when opening a directory with EDF.open()."""

    def test_open_directory_gives_helpful_error(self, unzipped_edf_dir):
        """EDF.open() on a directory gives a helpful error message."""
        with pytest.raises(EDFError, match="is a directory"):
            EDF.open(unzipped_edf_dir)

    def test_open_directory_suggests_from_directory(self, unzipped_edf_dir):
        """Error message suggests using from_directory()."""
        with pytest.raises(EDFError, match="from_directory"):
            EDF.open(unzipped_edf_dir)
