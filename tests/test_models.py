"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from edf.models import (
    Manifest,
    TaskCore,
    SubmissionCore,
    SubmissionIndex,
    GradeDistributions,
    ContentFormat,
    AdditionalDataDeclaration,
)


class TestManifest:
    """Tests for Manifest model."""

    def test_valid_manifest(self):
        """Create valid manifest."""
        m = Manifest(
            edf_version="1.0.0",
            task_id="550e8400-e29b-41d4-a716-446655440000",
            content_hash="sha256:" + "a" * 64,
            created_at=1736942400000,
            content_format=ContentFormat.MARKDOWN,
            submission_count=10,
            has_rubric=True,
            has_prompt=False,
        )
        assert m.edf_version == "1.0.0"
        assert m.submission_count == 10

    def test_invalid_task_id_not_uuid(self):
        """Reject non-UUID task_id."""
        with pytest.raises(ValidationError, match="task_id"):
            Manifest(
                edf_version="1.0.0",
                task_id="not-a-uuid",
                content_hash="sha256:" + "a" * 64,
                created_at=1736942400000,
                content_format=ContentFormat.MARKDOWN,
                submission_count=10,
            )

    def test_invalid_content_hash_no_prefix(self):
        """Reject content_hash without sha256: prefix."""
        with pytest.raises(ValidationError, match="content_hash"):
            Manifest(
                edf_version="1.0.0",
                task_id="550e8400-e29b-41d4-a716-446655440000",
                content_hash="a" * 64,
                created_at=1736942400000,
                content_format=ContentFormat.MARKDOWN,
                submission_count=10,
            )

    def test_invalid_content_hash_wrong_length(self):
        """Reject content_hash with wrong length."""
        with pytest.raises(ValidationError, match="content_hash"):
            Manifest(
                edf_version="1.0.0",
                task_id="550e8400-e29b-41d4-a716-446655440000",
                content_hash="sha256:abc",
                created_at=1736942400000,
                content_format=ContentFormat.MARKDOWN,
                submission_count=10,
            )

    def test_negative_submission_count(self):
        """Reject negative submission_count."""
        with pytest.raises(ValidationError):
            Manifest(
                edf_version="1.0.0",
                task_id="550e8400-e29b-41d4-a716-446655440000",
                content_hash="sha256:" + "a" * 64,
                created_at=1736942400000,
                content_format=ContentFormat.MARKDOWN,
                submission_count=-1,
            )

    def test_default_additional_data(self):
        """additional_data defaults to empty."""
        m = Manifest(
            edf_version="1.0.0",
            task_id="550e8400-e29b-41d4-a716-446655440000",
            content_hash="sha256:" + "a" * 64,
            created_at=1736942400000,
            content_format=ContentFormat.MARKDOWN,
            submission_count=0,
        )
        assert m.additional_data.task == []
        assert m.additional_data.submission == []

    def test_task_id_normalized_lowercase(self):
        """task_id is normalized to lowercase."""
        m = Manifest(
            edf_version="1.0.0",
            task_id="550E8400-E29B-41D4-A716-446655440000",
            content_hash="sha256:" + "a" * 64,
            created_at=1736942400000,
            content_format=ContentFormat.MARKDOWN,
            submission_count=0,
        )
        assert m.task_id == "550e8400-e29b-41d4-a716-446655440000"


class TestTaskCore:
    """Tests for TaskCore model."""

    def test_valid_task_core(self):
        """Create valid task core."""
        t = TaskCore(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            version=1,
            max_grade=20,
        )
        assert t.version == 1
        assert t.max_grade == 20

    def test_version_must_be_positive(self):
        """version must be >= 1."""
        with pytest.raises(ValidationError):
            TaskCore(
                task_id="550e8400-e29b-41d4-a716-446655440000",
                version=0,
                max_grade=20,
            )

    def test_max_grade_can_be_zero(self):
        """max_grade can be 0."""
        t = TaskCore(
            task_id="550e8400-e29b-41d4-a716-446655440000",
            version=1,
            max_grade=0,
        )
        assert t.max_grade == 0

    def test_max_grade_negative_rejected(self):
        """max_grade cannot be negative."""
        with pytest.raises(ValidationError):
            TaskCore(
                task_id="550e8400-e29b-41d4-a716-446655440000",
                version=1,
                max_grade=-1,
            )

    def test_invalid_task_id_rejected(self):
        """TaskCore rejects invalid task_id."""
        with pytest.raises(ValidationError, match="task_id"):
            TaskCore(
                task_id="not-a-valid-uuid",
                version=1,
                max_grade=20,
            )


class TestGradeDistributions:
    """Tests for GradeDistributions model."""

    def test_valid_distributions(self):
        """Create valid distributions."""
        d = GradeDistributions(
            optimistic=[0.5, 0.5],
            expected=[0.5, 0.5],
            pessimistic=[0.5, 0.5],
        )
        assert sum(d.optimistic) == pytest.approx(1.0)

    def test_must_sum_to_one(self):
        """Distributions must sum to 1.0."""
        with pytest.raises(ValidationError, match="sum to 1.0"):
            GradeDistributions(
                optimistic=[0.5, 0.3],  # sums to 0.8
                expected=[0.5, 0.5],
                pessimistic=[0.5, 0.5],
            )

    def test_negative_probability_rejected(self):
        """Negative probabilities rejected."""
        with pytest.raises(ValidationError, match="non-negative"):
            GradeDistributions(
                optimistic=[-0.5, 1.5],
                expected=[0.5, 0.5],
                pessimistic=[0.5, 0.5],
            )

    def test_validate_length(self):
        """validate_length checks distribution length."""
        d = GradeDistributions(
            optimistic=[0.5, 0.5],
            expected=[0.5, 0.5],
            pessimistic=[0.5, 0.5],
        )
        d.validate_length(max_grade=1)  # length should be 2

        with pytest.raises(ValueError, match="must have length 4"):
            d.validate_length(max_grade=3)

    def test_tolerance_for_sum(self):
        """Sum can be slightly off due to floating point."""
        # This should work with tolerance
        d = GradeDistributions(
            optimistic=[0.33333, 0.33333, 0.33334],
            expected=[0.33333, 0.33333, 0.33334],
            pessimistic=[0.33333, 0.33333, 0.33334],
        )
        assert d is not None


class TestSubmissionCore:
    """Tests for SubmissionCore model."""

    def test_valid_submission_core(self):
        """Create valid submission core."""
        s = SubmissionCore(
            submission_id="test_student",
            grade=5,
            grade_distributions=GradeDistributions(
                optimistic=[0.1] * 10,
                expected=[0.1] * 10,
                pessimistic=[0.1] * 10,
            ),
        )
        assert s.submission_id == "test_student"
        assert s.grade == 5

    def test_invalid_submission_id(self):
        """Reject submission_id with special characters."""
        with pytest.raises(ValidationError, match="submission_id"):
            SubmissionCore(
                submission_id="test-student",
                grade=5,
                grade_distributions=GradeDistributions(
                    optimistic=[0.5, 0.5],
                    expected=[0.5, 0.5],
                    pessimistic=[0.5, 0.5],
                ),
            )

    def test_validate_grade_range(self):
        """validate_grade_range checks grade and distributions."""
        s = SubmissionCore(
            submission_id="test",
            grade=5,
            grade_distributions=GradeDistributions(
                optimistic=[0.1] * 10,
                expected=[0.1] * 10,
                pessimistic=[0.1] * 10,
            ),
        )
        s.validate_grade_range(max_grade=9)  # grade 5 is valid

        with pytest.raises(ValueError, match="exceeds max_grade"):
            s.validate_grade_range(max_grade=4)


class TestSubmissionIndex:
    """Tests for SubmissionIndex model."""

    def test_valid_index(self):
        """Create valid submission index."""
        idx = SubmissionIndex(
            submission_ids=["student_a", "student_b", "student_c"]
        )
        assert len(idx.submission_ids) == 3

    def test_empty_index(self):
        """Empty submission list is valid."""
        idx = SubmissionIndex(submission_ids=[])
        assert len(idx.submission_ids) == 0

    def test_invalid_id_in_list(self):
        """Reject invalid IDs in list."""
        with pytest.raises(ValidationError, match="submission_id"):
            SubmissionIndex(
                submission_ids=["valid_id", "invalid-id"]
            )


class TestContentFormat:
    """Tests for ContentFormat enum."""

    def test_values(self):
        """Check enum values."""
        assert ContentFormat.MARKDOWN.value == "markdown"
        assert ContentFormat.PDF.value == "pdf"
        assert ContentFormat.IMAGES.value == "images"

    def test_from_string(self):
        """Create from string."""
        assert ContentFormat("markdown") == ContentFormat.MARKDOWN
        assert ContentFormat("pdf") == ContentFormat.PDF
        assert ContentFormat("images") == ContentFormat.IMAGES


class TestAdditionalDataDeclaration:
    """Tests for AdditionalDataDeclaration model."""

    def test_defaults_empty(self):
        """Defaults to empty lists."""
        d = AdditionalDataDeclaration()
        assert d.task == []
        assert d.submission == []

    def test_with_values(self):
        """Create with values."""
        d = AdditionalDataDeclaration(
            task=["school_id", "subject_code"],
            submission=["student_name"],
        )
        assert len(d.task) == 2
        assert len(d.submission) == 1
