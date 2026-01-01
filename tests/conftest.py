"""Shared fixtures for EDF tests."""

import pytest
import tempfile
import math
from pathlib import Path

from edf import EDF


def make_distribution(peak: int, max_grade: int, sigma: float = 2.0) -> list[float]:
    """Generate a Gaussian distribution for testing."""
    dist = [math.exp(-((i - peak) ** 2) / (2 * sigma ** 2)) for i in range(max_grade + 1)]
    total = sum(dist)
    return [p / total for p in dist]


@pytest.fixture
def tmp_edf_path(tmp_path):
    """Provide a temporary path for EDF files."""
    return tmp_path / "test.edf"


@pytest.fixture
def simple_edf():
    """Create a simple EDF with one submission."""
    edf = EDF(max_grade=10)
    edf.add_submission(
        submission_id="test_student",
        grade=7,
        optimistic=make_distribution(8, 10),
        expected=make_distribution(7, 10),
        pessimistic=make_distribution(6, 10),
        content="Test answer content",
    )
    return edf


@pytest.fixture
def full_edf():
    """Create an EDF with rubric, prompt, metadata, and multiple submissions."""
    edf = EDF(max_grade=20)
    edf.rubric = "# Rubric\n\n- Criterion 1: 10 points\n- Criterion 2: 10 points"
    edf.prompt = "# Assignment\n\nWrite an essay."
    edf.set_task_data(
        school_id="TEST-001",
        subject_code="TEST-101",
    )

    for i, (name, grade) in enumerate([("alice", 18), ("bob", 15), ("carol", 12)]):
        edf.add_submission(
            submission_id=f"student_{name}",
            grade=grade,
            optimistic=make_distribution(grade + 1, 20),
            expected=make_distribution(grade, 20),
            pessimistic=make_distribution(grade - 1, 20),
            content=f"Answer from {name}",
            student_name=name.title(),
            student_id=f"2025-{i:03d}",
        )

    return edf


@pytest.fixture
def saved_edf(full_edf, tmp_path):
    """Create and save a full EDF, returning the path."""
    path = tmp_path / "saved.edf"
    full_edf.save(path)
    return path


@pytest.fixture
def uniform_distribution():
    """Return a uniform distribution for max_grade=10."""
    return [1.0 / 11] * 11


@pytest.fixture
def unzipped_edf_dir(full_edf, tmp_path):
    """Create an unzipped EDF directory structure from full_edf."""
    import json
    import zipfile

    # First save the EDF to get proper manifest etc
    edf_path = tmp_path / "temp.edf"
    full_edf.save(edf_path)

    # Unzip to directory
    unzip_dir = tmp_path / "unzipped_edf"
    with zipfile.ZipFile(edf_path, "r") as zf:
        zf.extractall(unzip_dir)

    return unzip_dir


@pytest.fixture
def unzipped_pdf_edf_dir(tmp_path):
    """Create an unzipped EDF directory with PDF content."""
    import json

    unzip_dir = tmp_path / "pdf_edf"
    unzip_dir.mkdir()

    # Create manifest
    manifest = {
        "edf_version": "1.0.0",
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "content_hash": "sha256:" + "a" * 64,
        "created_at": 1700000000000,
        "content_format": "pdf",
        "submission_count": 1,
        "has_rubric": False,
        "has_prompt": False,
        "additional_data": {"task": [], "submission": []},
    }
    (unzip_dir / "manifest.json").write_text(json.dumps(manifest))

    # Create task
    task_dir = unzip_dir / "task"
    task_dir.mkdir()
    task_core = {"task_id": "550e8400-e29b-41d4-a716-446655440000", "version": 1, "max_grade": 10}
    (task_dir / "core.json").write_text(json.dumps(task_core))

    # Create submissions
    submissions_dir = unzip_dir / "submissions"
    submissions_dir.mkdir()
    (submissions_dir / "_index.json").write_text(json.dumps({"submission_ids": ["sub1"]}))

    sub_dir = submissions_dir / "sub1"
    sub_dir.mkdir()
    sub_core = {
        "submission_id": "sub1",
        "grade": 5,
        "grade_distributions": {
            "optimistic": [1/11] * 11,
            "expected": [1/11] * 11,
            "pessimistic": [1/11] * 11,
        },
    }
    (sub_dir / "core.json").write_text(json.dumps(sub_core))
    (sub_dir / "content.pdf").write_bytes(b"%PDF-1.4 fake pdf")

    return unzip_dir


@pytest.fixture
def unzipped_images_edf_dir(tmp_path):
    """Create an unzipped EDF directory with image content."""
    import json

    unzip_dir = tmp_path / "images_edf"
    unzip_dir.mkdir()

    # Create manifest
    manifest = {
        "edf_version": "1.0.0",
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "content_hash": "sha256:" + "b" * 64,
        "created_at": 1700000000000,
        "content_format": "images",
        "submission_count": 1,
        "has_rubric": False,
        "has_prompt": False,
        "additional_data": {"task": [], "submission": []},
    }
    (unzip_dir / "manifest.json").write_text(json.dumps(manifest))

    # Create task
    task_dir = unzip_dir / "task"
    task_dir.mkdir()
    task_core = {"task_id": "550e8400-e29b-41d4-a716-446655440000", "version": 1, "max_grade": 10}
    (task_dir / "core.json").write_text(json.dumps(task_core))

    # Create submissions
    submissions_dir = unzip_dir / "submissions"
    submissions_dir.mkdir()
    (submissions_dir / "_index.json").write_text(json.dumps({"submission_ids": ["sub1"]}))

    sub_dir = submissions_dir / "sub1"
    sub_dir.mkdir()
    sub_core = {
        "submission_id": "sub1",
        "grade": 5,
        "grade_distributions": {
            "optimistic": [1/11] * 11,
            "expected": [1/11] * 11,
            "pessimistic": [1/11] * 11,
        },
    }
    (sub_dir / "core.json").write_text(json.dumps(sub_core))

    pages_dir = sub_dir / "pages"
    pages_dir.mkdir()
    (pages_dir / "0.jpg").write_bytes(b"fake jpg 0")
    (pages_dir / "1.jpg").write_bytes(b"fake jpg 1")

    return unzip_dir


@pytest.fixture
def unzipped_edf_missing_files(tmp_path):
    """Create an unzipped EDF with manifest declaring files that don't exist."""
    import json

    unzip_dir = tmp_path / "missing_files_edf"
    unzip_dir.mkdir()

    # Create manifest that declares rubric, prompt, and additional_data
    # but we won't create those files
    manifest = {
        "edf_version": "1.0.0",
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "content_hash": "sha256:" + "c" * 64,
        "created_at": 1700000000000,
        "content_format": "markdown",
        "submission_count": 1,
        "has_rubric": True,  # Declared but file won't exist
        "has_prompt": True,  # Declared but file won't exist
        "additional_data": {"task": ["school_id"], "submission": ["student_name"]},
    }
    (unzip_dir / "manifest.json").write_text(json.dumps(manifest))

    # Create task (but no rubric.md, prompt.md, or additional_data.json)
    task_dir = unzip_dir / "task"
    task_dir.mkdir()
    task_core = {"task_id": "550e8400-e29b-41d4-a716-446655440000", "version": 1, "max_grade": 10}
    (task_dir / "core.json").write_text(json.dumps(task_core))

    # Create submissions (but no additional_data.json)
    submissions_dir = unzip_dir / "submissions"
    submissions_dir.mkdir()
    (submissions_dir / "_index.json").write_text(json.dumps({"submission_ids": ["sub1"]}))

    sub_dir = submissions_dir / "sub1"
    sub_dir.mkdir()
    sub_core = {
        "submission_id": "sub1",
        "grade": 5,
        "grade_distributions": {
            "optimistic": [1/11] * 11,
            "expected": [1/11] * 11,
            "pessimistic": [1/11] * 11,
        },
    }
    (sub_dir / "core.json").write_text(json.dumps(sub_core))
    (sub_dir / "content.md").write_text("Test content")

    return unzip_dir
