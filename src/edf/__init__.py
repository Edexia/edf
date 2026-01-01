"""
EDF - Edexia Data Format SDK

A Python library for reading and writing EDF files, which are ZIP archives
containing grading data for automated learning systems.
"""

from edf.exceptions import (
    EDFError,
    EDFValidationError,
    EDFStructureError,
    EDFConsistencyError,
)
from edf.models import (
    Manifest,
    TaskCore,
    GradeDistributions,
    SubmissionCore,
    SubmissionIndex,
    ContentFormat,
    AdditionalDataDeclaration,
)
from edf.reader import EDFReader
from edf.writer import EDFBuilder

__version__ = "0.1.0"

__all__ = [
    # Exceptions
    "EDFError",
    "EDFValidationError",
    "EDFStructureError",
    "EDFConsistencyError",
    # Models
    "Manifest",
    "TaskCore",
    "GradeDistributions",
    "SubmissionCore",
    "SubmissionIndex",
    "ContentFormat",
    "AdditionalDataDeclaration",
    # Reader/Writer
    "EDFReader",
    "EDFBuilder",
]
