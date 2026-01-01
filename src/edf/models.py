"""Pydantic models for EDF file schemas."""

from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field, field_validator, model_validator
import re


class ContentFormat(str, Enum):
    """Supported content formats for submissions."""

    MARKDOWN = "markdown"
    PDF = "pdf"
    IMAGES = "images"


class AdditionalDataDeclaration(BaseModel):
    """Declares which additional data attributes are used."""

    task: list[str] = Field(default_factory=list)
    submission: list[str] = Field(default_factory=list)


class Manifest(BaseModel):
    """The manifest.json schema declaring package structure."""

    edf_version: str = Field(description="Semantic version of the EDF format")
    task_id: str = Field(description="UUID v4 identifying this task")
    content_hash: str = Field(description="SHA256 hash prefixed with 'sha256:'")
    created_at: int = Field(description="Unix millisecond timestamp")
    content_format: ContentFormat
    submission_count: int = Field(ge=0)
    has_rubric: bool = False
    has_prompt: bool = False
    additional_data: AdditionalDataDeclaration = Field(
        default_factory=AdditionalDataDeclaration
    )

    @field_validator("content_hash")
    @classmethod
    def validate_content_hash(cls, v: str) -> str:
        if not v.startswith("sha256:"):
            raise ValueError("content_hash must be prefixed with 'sha256:'")
        hex_part = v[7:]
        if len(hex_part) != 64 or not all(c in "0123456789abcdef" for c in hex_part):
            raise ValueError("content_hash must contain a valid SHA256 hex string")
        return v

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        if not uuid_pattern.match(v):
            raise ValueError("task_id must be a valid UUID v4")
        return v.lower()


class TaskCore(BaseModel):
    """The task/core.json schema."""

    task_id: str = Field(description="Must match manifest task_id")
    version: int = Field(ge=1, description="Increments on content change")
    max_grade: int = Field(ge=0, description="Maximum possible grade")

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        if not uuid_pattern.match(v):
            raise ValueError("task_id must be a valid UUID v4")
        return v.lower()


class GradeDistributions(BaseModel):
    """Three probability distributions modeling different marker noise levels."""

    optimistic: list[float] = Field(description="Low-noise scenario (tight distribution)")
    expected: list[float] = Field(description="Medium-noise scenario (baseline)")
    pessimistic: list[float] = Field(description="High-noise scenario (wide distribution)")

    @field_validator("optimistic", "expected", "pessimistic")
    @classmethod
    def validate_probabilities(cls, v: list[float]) -> list[float]:
        if any(p < 0 for p in v):
            raise ValueError("All probabilities must be non-negative")
        total = sum(v)
        if abs(total - 1.0) > 0.0001:
            raise ValueError(f"Probabilities must sum to 1.0 (got {total})")
        return v

    def validate_length(self, max_grade: int) -> None:
        """Validate that all distributions have length max_grade + 1."""
        expected_len = max_grade + 1
        for name, dist in [
            ("optimistic", self.optimistic),
            ("expected", self.expected),
            ("pessimistic", self.pessimistic),
        ]:
            if len(dist) != expected_len:
                raise ValueError(
                    f"{name} distribution must have length {expected_len}, got {len(dist)}"
                )


class SubmissionCore(BaseModel):
    """The submissions/{id}/core.json schema."""

    submission_id: str = Field(description="Alphanumeric + underscores only")
    grade: int = Field(ge=0, description="Ground truth grade")
    grade_distributions: GradeDistributions

    @field_validator("submission_id")
    @classmethod
    def validate_submission_id(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "submission_id must contain only alphanumeric characters and underscores"
            )
        return v

    def validate_grade_range(self, max_grade: int) -> None:
        """Validate that grade is within [0, max_grade]."""
        if self.grade > max_grade:
            raise ValueError(
                f"grade {self.grade} exceeds max_grade {max_grade}"
            )
        self.grade_distributions.validate_length(max_grade)


class SubmissionIndex(BaseModel):
    """The submissions/_index.json schema."""

    submission_ids: list[str]

    @field_validator("submission_ids")
    @classmethod
    def validate_submission_ids(cls, v: list[str]) -> list[str]:
        for sid in v:
            if not re.match(r"^[a-zA-Z0-9_]+$", sid):
                raise ValueError(
                    f"submission_id '{sid}' must contain only alphanumeric characters and underscores"
                )
        return v
