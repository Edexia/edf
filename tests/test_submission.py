"""Tests for Submission class."""

import math
import pytest
from edf import EDF, ContentFormat
from edf.core import Submission
from edf.models import GradeDistributions


def make_distribution(peak: int, max_grade: int, sigma: float = 2.0) -> list[float]:
    """Generate a Gaussian distribution for testing."""
    dist = [math.exp(-((i - peak) ** 2) / (2 * sigma ** 2)) for i in range(max_grade + 1)]
    total = sum(dist)
    return [p / total for p in dist]


class TestSubmissionProperties:
    """Tests for Submission properties."""

    def test_id_property(self, simple_edf):
        """Submission id property."""
        sub = simple_edf.get_submission("test_student")
        assert sub.id == "test_student"

    def test_grade_property(self, simple_edf):
        """Submission grade property."""
        sub = simple_edf.get_submission("test_student")
        assert sub.grade == 7

    def test_distributions_property(self, simple_edf):
        """Submission distributions property."""
        sub = simple_edf.get_submission("test_student")
        assert isinstance(sub.distributions, GradeDistributions)
        assert len(sub.distributions.expected) == 11  # max_grade=10

    def test_content_format_markdown(self, simple_edf):
        """Content format detected as markdown."""
        sub = simple_edf.get_submission("test_student")
        assert sub.content_format == ContentFormat.MARKDOWN

    def test_content_format_pdf(self, uniform_distribution):
        """Content format detected as PDF."""
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content=b"%PDF-1.4",
        )
        sub = edf.get_submission("test")
        assert sub.content_format == ContentFormat.PDF

    def test_content_format_images(self, uniform_distribution):
        """Content format detected as images."""
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content=[b"img1", b"img2"],
        )
        sub = edf.get_submission("test")
        assert sub.content_format == ContentFormat.IMAGES

    def test_additional_data(self, full_edf):
        """Additional data accessible."""
        sub = full_edf.get_submission("student_alice")
        assert sub.additional["student_name"] == "Alice"
        assert sub.additional["student_id"] == "2025-000"


class TestSubmissionContentAccess:
    """Tests for Submission content access methods."""

    def test_get_markdown(self, simple_edf):
        """get_markdown returns content for markdown format."""
        sub = simple_edf.get_submission("test_student")
        content = sub.get_markdown()
        assert content == "Test answer content"

    def test_get_markdown_returns_none_for_pdf(self, uniform_distribution):
        """get_markdown returns None for PDF format."""
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content=b"%PDF-1.4",
        )
        sub = edf.get_submission("test")
        assert sub.get_markdown() is None

    def test_get_pdf(self, uniform_distribution):
        """get_pdf returns content for PDF format."""
        pdf_data = b"%PDF-1.4 test content"
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content=pdf_data,
        )
        sub = edf.get_submission("test")
        assert sub.get_pdf() == pdf_data

    def test_get_pdf_returns_none_for_markdown(self, simple_edf):
        """get_pdf returns None for markdown format."""
        sub = simple_edf.get_submission("test_student")
        assert sub.get_pdf() is None

    def test_get_images(self, uniform_distribution):
        """get_images returns content for images format."""
        images = [b"jpg1", b"jpg2", b"jpg3"]
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content=images,
        )
        sub = edf.get_submission("test")
        assert sub.get_images() == images

    def test_get_images_returns_none_for_markdown(self, simple_edf):
        """get_images returns None for markdown format."""
        sub = simple_edf.get_submission("test_student")
        assert sub.get_images() is None


class TestSubmissionRoundTrip:
    """Tests for submission content preservation through save/load."""

    def test_markdown_preserved(self, tmp_path, uniform_distribution):
        """Markdown content preserved through save/load."""
        content = "# Test\n\nThis is **markdown** content."
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content=content,
        )

        path = tmp_path / "test.edf"
        edf.save(path)

        with EDF.open(path) as loaded:
            sub = loaded.get_submission("test")
            assert sub.get_markdown() == content

    def test_pdf_preserved(self, tmp_path, uniform_distribution):
        """PDF content preserved through save/load."""
        pdf_data = b"%PDF-1.4\n%binary content here\x00\xff\xfe"
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content=pdf_data,
        )

        path = tmp_path / "test.edf"
        edf.save(path)

        with EDF.open(path) as loaded:
            sub = loaded.get_submission("test")
            assert sub.get_pdf() == pdf_data

    def test_images_preserved(self, tmp_path, uniform_distribution):
        """Image content preserved through save/load."""
        images = [b"\xff\xd8\xff page 1", b"\xff\xd8\xff page 2"]
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content=images,
        )

        path = tmp_path / "test.edf"
        edf.save(path)

        with EDF.open(path) as loaded:
            sub = loaded.get_submission("test")
            loaded_images = sub.get_images()
            assert loaded_images == images

    def test_additional_data_preserved(self, tmp_path, uniform_distribution):
        """Additional data preserved through save/load."""
        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=5,
            optimistic=uniform_distribution,
            expected=uniform_distribution,
            pessimistic=uniform_distribution,
            content="content",
            custom_field="custom_value",
            another_field=12345,
        )

        path = tmp_path / "test.edf"
        edf.save(path)

        with EDF.open(path) as loaded:
            sub = loaded.get_submission("test")
            assert sub.additional["custom_field"] == "custom_value"
            assert sub.additional["another_field"] == 12345

    def test_distributions_preserved(self, tmp_path):
        """Grade distributions preserved through save/load."""
        opt = [0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.3, 0.25, 0.1, 0.05]
        exp = [0.0, 0.0, 0.0, 0.0, 0.1, 0.15, 0.25, 0.25, 0.15, 0.1, 0.0]
        pes = [0.0, 0.0, 0.0, 0.1, 0.15, 0.2, 0.25, 0.15, 0.1, 0.05, 0.0]

        edf = EDF(max_grade=10)
        edf.add_submission(
            submission_id="test",
            grade=7,
            optimistic=opt,
            expected=exp,
            pessimistic=pes,
            content="content",
        )

        path = tmp_path / "test.edf"
        edf.save(path)

        with EDF.open(path) as loaded:
            sub = loaded.get_submission("test")
            for i in range(11):
                assert sub.distributions.optimistic[i] == pytest.approx(opt[i])
                assert sub.distributions.expected[i] == pytest.approx(exp[i])
                assert sub.distributions.pessimistic[i] == pytest.approx(pes[i])
