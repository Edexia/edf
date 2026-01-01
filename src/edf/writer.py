"""Writer/builder for EDF files."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from zipfile import ZipFile, ZIP_DEFLATED

from edf.models import ContentFormat


@dataclass
class SubmissionData:
    """Data for a single submission."""

    submission_id: str
    grade: int
    optimistic: list[float]
    expected: list[float]
    pessimistic: list[float]
    content: str | bytes | list[bytes]  # markdown, pdf, or list of images
    additional_data: dict[str, Any] = field(default_factory=dict)


class EDFBuilder:
    """
    Builder for creating EDF (Edexia Data Format) files.

    Usage:
        builder = EDFBuilder()
        builder.set_max_grade(20)
        builder.set_rubric("# Grading Criteria\\n...")
        builder.add_submission(
            submission_id="student_a",
            grade=15,
            optimistic=[...],
            expected=[...],
            pessimistic=[...],
            content="The student's answer...",
        )
        builder.write("output.edf")
    """

    EDF_VERSION = "0.1.0"

    def __init__(self, task_id: str | None = None):
        """
        Initialize a new EDF builder.

        Args:
            task_id: UUID v4 for the task. Auto-generated if not provided.
        """
        self._task_id = task_id or str(uuid.uuid4())
        self._version = 1
        self._max_grade: int | None = None
        self._rubric: str | None = None
        self._prompt: str | None = None
        self._task_additional: dict[str, Any] = {}
        self._submissions: list[SubmissionData] = []
        self._content_format: ContentFormat | None = None

    def set_version(self, version: int) -> EDFBuilder:
        """Set the task version number."""
        if version < 1:
            raise ValueError("version must be >= 1")
        self._version = version
        return self

    def set_max_grade(self, max_grade: int) -> EDFBuilder:
        """Set the maximum possible grade."""
        if max_grade < 0:
            raise ValueError("max_grade must be >= 0")
        self._max_grade = max_grade
        return self

    def set_rubric(self, rubric: str) -> EDFBuilder:
        """Set the rubric markdown content."""
        self._rubric = rubric
        return self

    def set_prompt(self, prompt: str) -> EDFBuilder:
        """Set the prompt markdown content."""
        self._prompt = prompt
        return self

    def set_task_data(self, **kwargs: Any) -> EDFBuilder:
        """Set additional task-level data attributes."""
        self._task_additional.update(kwargs)
        return self

    def add_submission(
        self,
        submission_id: str,
        grade: int,
        optimistic: list[float],
        expected: list[float],
        pessimistic: list[float],
        content: str | bytes | list[bytes],
        **additional: Any,
    ) -> EDFBuilder:
        """
        Add a submission to the EDF file.

        Args:
            submission_id: Unique identifier (alphanumeric + underscores)
            grade: The ground truth grade
            optimistic: Probability distribution (favorable interpretation)
            expected: Probability distribution (most likely outcome)
            pessimistic: Probability distribution (strict interpretation)
            content: Either a markdown string, PDF bytes, or list of JPEG bytes
            **additional: Additional submission-level attributes

        Returns:
            self for method chaining
        """
        # Validate submission_id
        if not submission_id or not all(
            c.isalnum() or c == "_" for c in submission_id
        ):
            raise ValueError(
                "submission_id must be non-empty and contain only alphanumeric characters and underscores"
            )

        # Detect content format
        if isinstance(content, str):
            fmt = ContentFormat.MARKDOWN
        elif isinstance(content, bytes):
            fmt = ContentFormat.PDF
        elif isinstance(content, list) and all(isinstance(b, bytes) for b in content):
            fmt = ContentFormat.IMAGES
        else:
            raise ValueError(
                "content must be a string (markdown), bytes (pdf), or list of bytes (images)"
            )

        # Ensure consistent format across submissions
        if self._content_format is None:
            self._content_format = fmt
        elif self._content_format != fmt:
            raise ValueError(
                f"All submissions must use the same content format. "
                f"Expected {self._content_format.value}, got {fmt.value}"
            )

        self._submissions.append(
            SubmissionData(
                submission_id=submission_id,
                grade=grade,
                optimistic=optimistic,
                expected=expected,
                pessimistic=pessimistic,
                content=content,
                additional_data=additional,
            )
        )
        return self

    def _validate(self) -> None:
        """Validate the builder state before writing."""
        if self._max_grade is None:
            raise ValueError("max_grade must be set before writing")

        if not self._submissions:
            raise ValueError("At least one submission is required")

        expected_len = self._max_grade + 1
        for sub in self._submissions:
            # Validate grade range
            if sub.grade < 0 or sub.grade > self._max_grade:
                raise ValueError(
                    f"Submission {sub.submission_id}: grade {sub.grade} out of range [0, {self._max_grade}]"
                )

            # Validate distribution lengths
            for name, dist in [
                ("optimistic", sub.optimistic),
                ("expected", sub.expected),
                ("pessimistic", sub.pessimistic),
            ]:
                if len(dist) != expected_len:
                    raise ValueError(
                        f"Submission {sub.submission_id}: {name} distribution must have "
                        f"length {expected_len}, got {len(dist)}"
                    )
                if any(p < 0 for p in dist):
                    raise ValueError(
                        f"Submission {sub.submission_id}: {name} contains negative probabilities"
                    )
                total = sum(dist)
                if abs(total - 1.0) > 0.0001:
                    raise ValueError(
                        f"Submission {sub.submission_id}: {name} probabilities sum to {total}, expected 1.0"
                    )

    def _compute_content_hash(self, files: dict[str, bytes]) -> str:
        """
        Compute the canonical content hash.

        Algorithm:
        1. Collect content files (rubric, prompt, submission content)
        2. Sort paths alphabetically
        3. Concatenate as {path}\\x00{content}\\x00 for each file
        4. SHA256 the result
        5. Prefix with "sha256:"
        """
        content_paths = []

        if self._rubric is not None:
            content_paths.append("task/rubric.md")
        if self._prompt is not None:
            content_paths.append("task/prompt.md")

        for path in files:
            if path.startswith("submissions/") and (
                path.endswith("/content.md")
                or path.endswith("/content.pdf")
                or "/pages/" in path
            ):
                content_paths.append(path)

        content_paths.sort()

        hasher = hashlib.sha256()
        for path in content_paths:
            hasher.update(path.encode("utf-8"))
            hasher.update(b"\x00")
            hasher.update(files[path])
            hasher.update(b"\x00")

        return f"sha256:{hasher.hexdigest()}"

    def write(self, path: str | Path) -> None:
        """
        Write the EDF file to disk.

        Args:
            path: Output path for the .edf file
        """
        self._validate()

        # Collect all additional data attribute names
        task_attrs = sorted(self._task_additional.keys())
        submission_attrs: set[str] = set()
        for sub in self._submissions:
            submission_attrs.update(sub.additional_data.keys())
        submission_attrs_list = sorted(submission_attrs)

        # Build file contents
        files: dict[str, bytes] = {}

        # task/core.json
        files["task/core.json"] = json.dumps(
            {
                "task_id": self._task_id,
                "version": self._version,
                "max_grade": self._max_grade,
            },
            indent=2,
        ).encode("utf-8")

        # task/rubric.md
        if self._rubric is not None:
            files["task/rubric.md"] = self._rubric.encode("utf-8")

        # task/prompt.md
        if self._prompt is not None:
            files["task/prompt.md"] = self._prompt.encode("utf-8")

        # task/additional_data.json
        if self._task_additional:
            files["task/additional_data.json"] = json.dumps(
                self._task_additional, indent=2
            ).encode("utf-8")

        # submissions/_index.json
        submission_ids = [sub.submission_id for sub in self._submissions]
        files["submissions/_index.json"] = json.dumps(
            {"submission_ids": submission_ids}, indent=2
        ).encode("utf-8")

        # Each submission
        for sub in self._submissions:
            base = f"submissions/{sub.submission_id}"

            # core.json
            files[f"{base}/core.json"] = json.dumps(
                {
                    "submission_id": sub.submission_id,
                    "grade": sub.grade,
                    "grade_distributions": {
                        "optimistic": sub.optimistic,
                        "expected": sub.expected,
                        "pessimistic": sub.pessimistic,
                    },
                },
                indent=2,
            ).encode("utf-8")

            # additional_data.json
            if submission_attrs_list:
                # Ensure all declared attrs are present (null if not provided)
                additional = {attr: sub.additional_data.get(attr) for attr in submission_attrs_list}
                files[f"{base}/additional_data.json"] = json.dumps(
                    additional, indent=2
                ).encode("utf-8")

            # Content
            if isinstance(sub.content, str):
                files[f"{base}/content.md"] = sub.content.encode("utf-8")
            elif isinstance(sub.content, bytes):
                files[f"{base}/content.pdf"] = sub.content
            elif isinstance(sub.content, list):
                for i, img_bytes in enumerate(sub.content):
                    files[f"{base}/pages/{i}.jpg"] = img_bytes

        # Compute content hash
        content_hash = self._compute_content_hash(files)

        # manifest.json (must be created after we know the hash)
        manifest = {
            "edf_version": self.EDF_VERSION,
            "task_id": self._task_id,
            "content_hash": content_hash,
            "created_at": int(time.time() * 1000),
            "content_format": self._content_format.value,
            "submission_count": len(self._submissions),
            "has_rubric": self._rubric is not None,
            "has_prompt": self._prompt is not None,
            "additional_data": {
                "task": task_attrs,
                "submission": submission_attrs_list,
            },
        }
        files["manifest.json"] = json.dumps(manifest, indent=2).encode("utf-8")

        # Write the ZIP
        with ZipFile(path, "w", ZIP_DEFLATED) as zf:
            for file_path, content in sorted(files.items()):
                zf.writestr(file_path, content)
