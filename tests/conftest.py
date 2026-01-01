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
