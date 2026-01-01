"""Core EDF class for reading and writing EDF files."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator
from zipfile import ZipFile, ZIP_DEFLATED

from edf.exceptions import EDFError, EDFValidationError
from edf.models import (
    ContentFormat,
    GradeDistributions,
    Manifest,
    SubmissionCore,
    SubmissionIndex,
    TaskCore,
    AdditionalDataDeclaration,
)
from edf.validation import validate_edf


EDF_VERSION = "1.0.0"

# Sentinel UUID for ephemeral EDFs (loaded from unzipped directories)
EPHEMERAL_TASK_ID = "00000000-0000-0000-0000-000000000000"
EPHEMERAL_VERSION = 0


@dataclass
class Submission:
    """A submission within an EDF file."""

    id: str
    grade: int
    distributions: GradeDistributions
    content: str | bytes | list[bytes]
    additional: dict[str, Any] = field(default_factory=dict)

    @property
    def content_format(self) -> ContentFormat:
        if isinstance(self.content, str):
            return ContentFormat.MARKDOWN
        elif isinstance(self.content, bytes):
            return ContentFormat.PDF
        else:
            return ContentFormat.IMAGES

    def get_markdown(self) -> str | None:
        """Get content as markdown, or None if not markdown format."""
        return self.content if isinstance(self.content, str) else None

    def get_pdf(self) -> bytes | None:
        """Get content as PDF bytes, or None if not PDF format."""
        return self.content if isinstance(self.content, bytes) and not isinstance(self.content, list) else None

    def get_images(self) -> list[bytes] | None:
        """Get content as list of image bytes, or None if not images format."""
        return self.content if isinstance(self.content, list) else None


class EDF:
    """
    Edexia Data Format file.

    Create a new EDF:
        edf = EDF(max_grade=20)
        edf.rubric = "# Grading Criteria..."
        edf.add_submission("student_1", grade=15, ...)
        edf.save("output.edf")

    Open an existing EDF:
        edf = EDF.open("file.edf")
        print(edf.max_grade)
        for sub in edf.submissions:
            print(sub.id, sub.grade)
    """

    def __init__(
        self,
        max_grade: int,
        task_id: str | None = None,
        version: int = 1,
        edf_version: str = EDF_VERSION,
    ):
        """
        Create a new EDF.

        Args:
            max_grade: Maximum possible grade (0 to max_grade inclusive)
            task_id: UUID v4 for this task. Auto-generated if not provided.
            version: Task version number (default 1)
            edf_version: EDF format version (default "1.0.0")
        """
        self._task_id = task_id or str(uuid.uuid4())
        self._version = version
        self._edf_version = edf_version
        self._max_grade = max_grade
        self._rubric: str | None = None
        self._prompt: str | None = None
        self._task_additional: dict[str, Any] = {}
        self._submissions: dict[str, Submission] = {}
        self._created_at: int | None = None
        self._content_hash: str | None = None
        self._zf: ZipFile | None = None

    @classmethod
    def open(cls, path: str | Path, validate: bool = True) -> EDF:
        """
        Open an existing EDF file.

        Args:
            path: Path to the .edf file
            validate: Whether to validate the file (default True)

        Returns:
            An EDF instance with the file's contents loaded
        """
        path = Path(path)
        if path.is_dir():
            raise EDFError(
                f"'{path}' is a directory. Use EDF.from_directory() with "
                "dangerously_load_unzipped_edf=True to load from an unzipped directory."
            )
        zf = ZipFile(path, "r")

        try:
            if validate:
                errors, warnings = validate_edf(zf)
                if errors:
                    zf.close()
                    raise EDFValidationError(
                        f"EDF validation failed with {len(errors)} error(s)",
                        errors=errors,
                    )

            # Read manifest
            manifest_data = json.loads(zf.read("manifest.json"))
            manifest = Manifest.model_validate(manifest_data)

            # Read task core
            task_data = json.loads(zf.read("task/core.json"))
            task_core = TaskCore.model_validate(task_data)

            # Create instance
            edf = cls(
                max_grade=task_core.max_grade,
                task_id=manifest.task_id,
                version=task_core.version,
                edf_version=manifest.edf_version,
            )
            edf._created_at = manifest.created_at
            edf._content_hash = manifest.content_hash
            edf._zf = zf

            # Read rubric and prompt
            if manifest.has_rubric:
                edf._rubric = zf.read("task/rubric.md").decode("utf-8")
            if manifest.has_prompt:
                edf._prompt = zf.read("task/prompt.md").decode("utf-8")

            # Read task additional data
            if manifest.additional_data.task:
                edf._task_additional = json.loads(zf.read("task/additional_data.json"))

            # Read submissions
            index_data = json.loads(zf.read("submissions/_index.json"))
            index = SubmissionIndex.model_validate(index_data)

            for sid in index.submission_ids:
                sub_core_data = json.loads(zf.read(f"submissions/{sid}/core.json"))
                sub_core = SubmissionCore.model_validate(sub_core_data)

                # Read additional data
                sub_additional = {}
                if manifest.additional_data.submission:
                    sub_additional = json.loads(
                        zf.read(f"submissions/{sid}/additional_data.json")
                    )

                # Read content
                if manifest.content_format == ContentFormat.MARKDOWN:
                    content = zf.read(f"submissions/{sid}/content.md").decode("utf-8")
                elif manifest.content_format == ContentFormat.PDF:
                    content = zf.read(f"submissions/{sid}/content.pdf")
                else:  # IMAGES
                    content = []
                    i = 0
                    while True:
                        try:
                            img = zf.read(f"submissions/{sid}/pages/{i}.jpg")
                            content.append(img)
                            i += 1
                        except KeyError:
                            break

                edf._submissions[sid] = Submission(
                    id=sid,
                    grade=sub_core.grade,
                    distributions=sub_core.grade_distributions,
                    content=content,
                    additional=sub_additional,
                )

            return edf

        except Exception:
            zf.close()
            raise

    @classmethod
    def from_directory(
        cls,
        path: str | Path,
        dangerously_load_unzipped_edf: bool = False,
    ) -> EDF:
        """
        Load an EDF from an unzipped directory.

        This creates an ephemeral EDF with a sentinel task_id and version=0.
        The EDF cannot be traced back to any versioned source.
        Useful for development and testing where you want to edit files directly.

        Args:
            path: Path to the unzipped EDF directory (containing manifest.json)
            dangerously_load_unzipped_edf: Must be True to acknowledge the risks

        Returns:
            An ephemeral EDF instance

        Raises:
            ValueError: If dangerously_load_unzipped_edf is not True
            EDFError: If the directory structure is invalid
        """
        if not dangerously_load_unzipped_edf:
            raise ValueError(
                "Loading unzipped EDFs bypasses integrity checks and versioning. "
                "Set dangerously_load_unzipped_edf=True to proceed."
            )

        path = Path(path)
        if not path.is_dir():
            raise EDFError(f"Not a directory: {path}")

        # Read manifest
        manifest_path = path / "manifest.json"
        if not manifest_path.exists():
            raise EDFError(f"Missing manifest.json in {path}")

        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = Manifest.model_validate(manifest_data)

        # Read task core
        task_path = path / "task" / "core.json"
        if not task_path.exists():
            raise EDFError(f"Missing task/core.json in {path}")

        task_data = json.loads(task_path.read_text(encoding="utf-8"))
        task_core = TaskCore.model_validate(task_data)

        # Create ephemeral instance
        edf = cls(
            max_grade=task_core.max_grade,
            task_id=EPHEMERAL_TASK_ID,
            version=EPHEMERAL_VERSION,
            edf_version=manifest.edf_version,
        )
        edf._created_at = None  # Ephemeral EDFs have no created_at
        edf._content_hash = None  # No hash for ephemeral EDFs

        # Read rubric and prompt
        if manifest.has_rubric:
            rubric_path = path / "task" / "rubric.md"
            if rubric_path.exists():
                edf._rubric = rubric_path.read_text(encoding="utf-8")

        if manifest.has_prompt:
            prompt_path = path / "task" / "prompt.md"
            if prompt_path.exists():
                edf._prompt = prompt_path.read_text(encoding="utf-8")

        # Read task additional data
        if manifest.additional_data.task:
            additional_path = path / "task" / "additional_data.json"
            if additional_path.exists():
                edf._task_additional = json.loads(
                    additional_path.read_text(encoding="utf-8")
                )

        # Read submissions
        index_path = path / "submissions" / "_index.json"
        if not index_path.exists():
            raise EDFError(f"Missing submissions/_index.json in {path}")

        index_data = json.loads(index_path.read_text(encoding="utf-8"))
        index = SubmissionIndex.model_validate(index_data)

        for sid in index.submission_ids:
            sub_dir = path / "submissions" / sid
            sub_core_path = sub_dir / "core.json"
            if not sub_core_path.exists():
                raise EDFError(f"Missing submissions/{sid}/core.json in {path}")

            sub_core_data = json.loads(sub_core_path.read_text(encoding="utf-8"))
            sub_core = SubmissionCore.model_validate(sub_core_data)

            # Read additional data
            sub_additional = {}
            if manifest.additional_data.submission:
                additional_path = sub_dir / "additional_data.json"
                if additional_path.exists():
                    sub_additional = json.loads(
                        additional_path.read_text(encoding="utf-8")
                    )

            # Read content
            if manifest.content_format == ContentFormat.MARKDOWN:
                content_path = sub_dir / "content.md"
                content = content_path.read_text(encoding="utf-8")
            elif manifest.content_format == ContentFormat.PDF:
                content_path = sub_dir / "content.pdf"
                content = content_path.read_bytes()
            else:  # IMAGES
                content = []
                pages_dir = sub_dir / "pages"
                i = 0
                while True:
                    img_path = pages_dir / f"{i}.jpg"
                    if not img_path.exists():
                        break
                    content.append(img_path.read_bytes())
                    i += 1

            edf._submissions[sid] = Submission(
                id=sid,
                grade=sub_core.grade,
                distributions=sub_core.grade_distributions,
                content=content,
                additional=sub_additional,
            )

        return edf

    def close(self) -> None:
        """Close the underlying ZIP file if opened from disk."""
        if self._zf:
            self._zf.close()
            self._zf = None

    def __enter__(self) -> EDF:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # Properties

    @property
    def task_id(self) -> str:
        """UUID v4 identifying this task."""
        return self._task_id

    @property
    def version(self) -> int:
        """Task version number."""
        return self._version

    @version.setter
    def version(self, value: int) -> None:
        if value < 1:
            raise ValueError("version must be >= 1")
        self._version = value

    @property
    def edf_version(self) -> str:
        """EDF format version."""
        return self._edf_version

    @property
    def max_grade(self) -> int:
        """Maximum possible grade."""
        return self._max_grade

    @property
    def rubric(self) -> str | None:
        """Rubric markdown content."""
        return self._rubric

    @rubric.setter
    def rubric(self, value: str | None) -> None:
        self._rubric = value

    @property
    def prompt(self) -> str | None:
        """Prompt markdown content."""
        return self._prompt

    @prompt.setter
    def prompt(self, value: str | None) -> None:
        self._prompt = value

    @property
    def task_data(self) -> dict[str, Any]:
        """Additional task-level attributes."""
        return self._task_additional

    @property
    def created_at(self) -> int | None:
        """Unix millisecond timestamp when file was created. None if not yet saved."""
        return self._created_at

    @property
    def content_hash(self) -> str | None:
        """SHA256 content hash. None if not yet saved."""
        return self._content_hash

    @property
    def submissions(self) -> list[Submission]:
        """List of all submissions."""
        return list(self._submissions.values())

    @property
    def submission_ids(self) -> list[str]:
        """List of all submission IDs."""
        return list(self._submissions.keys())

    @property
    def content_format(self) -> ContentFormat | None:
        """Content format, or None if no submissions yet."""
        if not self._submissions:
            return None
        return next(iter(self._submissions.values())).content_format

    @property
    def is_ephemeral(self) -> bool:
        """True if this EDF was loaded from an unzipped directory."""
        return self._task_id == EPHEMERAL_TASK_ID

    # Methods

    def set_task_data(self, **kwargs: Any) -> EDF:
        """Set additional task-level attributes."""
        self._task_additional.update(kwargs)
        return self

    def get_submission(self, submission_id: str) -> Submission:
        """Get a submission by ID. Raises KeyError if not found."""
        return self._submissions[submission_id]

    def add_submission(
        self,
        submission_id: str,
        grade: int,
        optimistic: list[float],
        expected: list[float],
        pessimistic: list[float],
        content: str | bytes | list[bytes],
        **additional: Any,
    ) -> EDF:
        """
        Add a submission.

        Args:
            submission_id: Unique ID (alphanumeric + underscores)
            grade: Ground truth grade in [0, max_grade]
            optimistic: Optimistic probability distribution
            expected: Expected probability distribution
            pessimistic: Pessimistic probability distribution
            content: Markdown string, PDF bytes, or list of JPEG bytes
            **additional: Additional submission attributes

        Returns:
            self for method chaining
        """
        # Validate ID
        if not submission_id or not all(c.isalnum() or c == "_" for c in submission_id):
            raise ValueError("submission_id must be alphanumeric with underscores only")

        if submission_id in self._submissions:
            raise ValueError(f"Submission '{submission_id}' already exists")

        # Detect and validate content format
        if isinstance(content, str):
            fmt = ContentFormat.MARKDOWN
        elif isinstance(content, bytes):
            fmt = ContentFormat.PDF
        elif isinstance(content, list) and all(isinstance(b, bytes) for b in content):
            fmt = ContentFormat.IMAGES
        else:
            raise ValueError("content must be str (markdown), bytes (pdf), or list[bytes] (images)")

        # Check format consistency
        if self._submissions:
            existing_fmt = next(iter(self._submissions.values())).content_format
            if fmt != existing_fmt:
                raise ValueError(
                    f"Content format mismatch: expected {existing_fmt.value}, got {fmt.value}"
                )

        # Validate grade
        if grade < 0 or grade > self._max_grade:
            raise ValueError(f"grade must be in [0, {self._max_grade}]")

        # Create and validate distributions
        distributions = GradeDistributions(
            optimistic=optimistic,
            expected=expected,
            pessimistic=pessimistic,
        )
        distributions.validate_length(self._max_grade)

        self._submissions[submission_id] = Submission(
            id=submission_id,
            grade=grade,
            distributions=distributions,
            content=content,
            additional=additional,
        )

        return self

    def remove_submission(self, submission_id: str) -> EDF:
        """Remove a submission by ID. Raises KeyError if not found."""
        del self._submissions[submission_id]
        return self

    def _compute_content_hash(self, files: dict[str, bytes]) -> str:
        """Compute the canonical content hash."""
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

    def save(self, path: str | Path) -> None:
        """
        Save the EDF to a file.

        If saving an ephemeral EDF (loaded from directory), a new UUID and
        version will be auto-generated, and a warning will be printed.

        Args:
            path: Output path for the .edf file
        """
        if not self._submissions:
            raise ValueError("Cannot save EDF with no submissions")

        # Auto-generate UUID for ephemeral EDFs
        if self.is_ephemeral:
            import sys
            new_id = str(uuid.uuid4())
            print(
                f"Warning: Saving ephemeral EDF. "
                f"Generated new task_id: {new_id}",
                file=sys.stderr,
            )
            self._task_id = new_id
            self._version = 1

        # Collect additional data attribute names
        task_attrs = sorted(self._task_additional.keys())
        submission_attrs: set[str] = set()
        for sub in self._submissions.values():
            submission_attrs.update(sub.additional.keys())
        submission_attrs_list = sorted(submission_attrs)

        # Build files
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
        submission_ids = list(self._submissions.keys())
        files["submissions/_index.json"] = json.dumps(
            {"submission_ids": submission_ids}, indent=2
        ).encode("utf-8")

        # Each submission
        for sub in self._submissions.values():
            base = f"submissions/{sub.id}"

            # core.json
            files[f"{base}/core.json"] = json.dumps(
                {
                    "submission_id": sub.id,
                    "grade": sub.grade,
                    "grade_distributions": {
                        "optimistic": sub.distributions.optimistic,
                        "expected": sub.distributions.expected,
                        "pessimistic": sub.distributions.pessimistic,
                    },
                },
                indent=2,
            ).encode("utf-8")

            # additional_data.json
            if submission_attrs_list:
                additional = {attr: sub.additional.get(attr) for attr in submission_attrs_list}
                files[f"{base}/additional_data.json"] = json.dumps(
                    additional, indent=2
                ).encode("utf-8")

            # Content
            if isinstance(sub.content, str):
                files[f"{base}/content.md"] = sub.content.encode("utf-8")
            elif isinstance(sub.content, list):
                for i, img_bytes in enumerate(sub.content):
                    files[f"{base}/pages/{i}.jpg"] = img_bytes
            else:
                files[f"{base}/content.pdf"] = sub.content

        # Compute content hash
        self._content_hash = self._compute_content_hash(files)
        self._created_at = int(time.time() * 1000)

        # manifest.json
        manifest = {
            "edf_version": self._edf_version,
            "task_id": self._task_id,
            "content_hash": self._content_hash,
            "created_at": self._created_at,
            "content_format": self.content_format.value,
            "submission_count": len(self._submissions),
            "has_rubric": self._rubric is not None,
            "has_prompt": self._prompt is not None,
            "additional_data": {
                "task": task_attrs,
                "submission": submission_attrs_list,
            },
        }
        files["manifest.json"] = json.dumps(manifest, indent=2).encode("utf-8")

        # Write ZIP
        with ZipFile(path, "w", ZIP_DEFLATED) as zf:
            for file_path, content in sorted(files.items()):
                zf.writestr(file_path, content)
