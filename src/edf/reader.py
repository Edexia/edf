"""Reader for EDF files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from zipfile import ZipFile

from edf.exceptions import EDFStructureError, EDFValidationError
from edf.models import (
    ContentFormat,
    GradeDistributions,
    Manifest,
    SubmissionCore,
    SubmissionIndex,
    TaskCore,
)
from edf.validation import validate_edf


@dataclass
class Task:
    """Represents the task data from an EDF file."""

    core: TaskCore
    additional_data: dict[str, Any]
    rubric: str | None
    prompt: str | None


@dataclass
class Submission:
    """Represents a single submission from an EDF file."""

    core: SubmissionCore
    additional_data: dict[str, Any]
    content_format: ContentFormat
    _reader: EDFReader
    _id: str

    @property
    def submission_id(self) -> str:
        return self.core.submission_id

    @property
    def grade(self) -> int:
        return self.core.grade

    @property
    def grade_distributions(self) -> GradeDistributions:
        return self.core.grade_distributions

    def get_content_markdown(self) -> str | None:
        """Get content as markdown string, if format is markdown."""
        if self.content_format != ContentFormat.MARKDOWN:
            return None
        path = f"submissions/{self._id}/content.md"
        return self._reader._read_text(path)

    def get_content_pdf(self) -> bytes | None:
        """Get content as PDF bytes, if format is PDF."""
        if self.content_format != ContentFormat.PDF:
            return None
        path = f"submissions/{self._id}/content.pdf"
        return self._reader._read_bytes(path)

    def get_content_images(self) -> list[bytes] | None:
        """Get content as list of JPEG image bytes, if format is images."""
        if self.content_format != ContentFormat.IMAGES:
            return None
        images = []
        i = 0
        while True:
            path = f"submissions/{self._id}/pages/{i}.jpg"
            try:
                data = self._reader._read_bytes(path)
                images.append(data)
                i += 1
            except KeyError:
                break
        return images if images else None

    def list_page_files(self) -> list[str]:
        """List all page files for image content."""
        if self.content_format != ContentFormat.IMAGES:
            return []
        prefix = f"submissions/{self._id}/pages/"
        return sorted(
            [n for n in self._reader._zf.namelist() if n.startswith(prefix)]
        )


class EDFReader:
    """
    Reader for EDF (Edexia Data Format) files.

    Usage:
        with EDFReader.open("file.edf") as reader:
            print(reader.manifest.task_id)
            for submission in reader.iter_submissions():
                print(submission.grade)
    """

    def __init__(self, zf: ZipFile, validate: bool = True):
        """
        Initialize the reader with an open ZipFile.

        Use EDFReader.open() for the recommended way to open files.
        """
        self._zf = zf
        self._manifest: Manifest | None = None
        self._task: Task | None = None
        self._index: SubmissionIndex | None = None
        self._submissions: dict[str, Submission] = {}

        if validate:
            errors, warnings = validate_edf(zf)
            if errors:
                raise EDFValidationError(
                    f"EDF validation failed with {len(errors)} error(s)",
                    errors=errors,
                )

    @classmethod
    def open(cls, path: str | Path, validate: bool = True) -> EDFReader:
        """
        Open an EDF file for reading.

        Args:
            path: Path to the .edf file
            validate: If True, validate the file on open (default True)

        Returns:
            An EDFReader instance (use as context manager)
        """
        zf = ZipFile(path, "r")
        try:
            return cls(zf, validate=validate)
        except Exception:
            zf.close()
            raise

    def close(self) -> None:
        """Close the underlying ZIP file."""
        self._zf.close()

    def __enter__(self) -> EDFReader:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _read_text(self, path: str) -> str:
        """Read a text file from the archive."""
        return self._zf.read(path).decode("utf-8")

    def _read_bytes(self, path: str) -> bytes:
        """Read a binary file from the archive."""
        return self._zf.read(path)

    def _read_json(self, path: str) -> Any:
        """Read and parse a JSON file from the archive."""
        return json.loads(self._read_text(path))

    @property
    def manifest(self) -> Manifest:
        """Get the manifest."""
        if self._manifest is None:
            data = self._read_json("manifest.json")
            self._manifest = Manifest.model_validate(data)
        return self._manifest

    @property
    def task(self) -> Task:
        """Get the task data."""
        if self._task is None:
            core_data = self._read_json("task/core.json")
            core = TaskCore.model_validate(core_data)

            additional: dict[str, Any] = {}
            if self.manifest.additional_data.task:
                additional = self._read_json("task/additional_data.json")

            rubric = None
            if self.manifest.has_rubric:
                rubric = self._read_text("task/rubric.md")

            prompt = None
            if self.manifest.has_prompt:
                prompt = self._read_text("task/prompt.md")

            self._task = Task(
                core=core,
                additional_data=additional,
                rubric=rubric,
                prompt=prompt,
            )
        return self._task

    @property
    def submission_ids(self) -> list[str]:
        """Get the list of submission IDs."""
        if self._index is None:
            data = self._read_json("submissions/_index.json")
            self._index = SubmissionIndex.model_validate(data)
        return self._index.submission_ids

    def get_submission(self, submission_id: str) -> Submission:
        """
        Get a specific submission by ID.

        Args:
            submission_id: The submission identifier

        Returns:
            A Submission object

        Raises:
            KeyError: If submission_id is not found
        """
        if submission_id not in self.submission_ids:
            raise KeyError(f"Submission '{submission_id}' not found")

        if submission_id not in self._submissions:
            core_data = self._read_json(f"submissions/{submission_id}/core.json")
            core = SubmissionCore.model_validate(core_data)

            additional: dict[str, Any] = {}
            if self.manifest.additional_data.submission:
                additional = self._read_json(
                    f"submissions/{submission_id}/additional_data.json"
                )

            self._submissions[submission_id] = Submission(
                core=core,
                additional_data=additional,
                content_format=self.manifest.content_format,
                _reader=self,
                _id=submission_id,
            )

        return self._submissions[submission_id]

    def iter_submissions(self) -> Iterator[Submission]:
        """
        Iterate over all submissions.

        Yields:
            Submission objects, one per submission in the file
        """
        for sid in self.submission_ids:
            yield self.get_submission(sid)

    @property
    def rubric(self) -> str | None:
        """Get the rubric markdown, if present."""
        return self.task.rubric

    @property
    def prompt(self) -> str | None:
        """Get the prompt markdown, if present."""
        return self.task.prompt
