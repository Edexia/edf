"""
EDF - Edexia Data Format SDK

A Python library for reading and writing EDF files, which are ZIP archives
containing grading data for automated learning systems.
"""

from edf.core import EDF, Submission, EDF_VERSION, EPHEMERAL_TASK_ID, EPHEMERAL_VERSION
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

__version__ = "0.3.0"

__all__ = [
    # Main class
    "EDF",
    "Submission",
    "EDF_VERSION",
    "EPHEMERAL_TASK_ID",
    "EPHEMERAL_VERSION",
    # Exceptions
    "EDFError",
    "EDFValidationError",
    "EDFStructureError",
    "EDFConsistencyError",
    # Models (for advanced usage)
    "Manifest",
    "TaskCore",
    "GradeDistributions",
    "SubmissionCore",
    "SubmissionIndex",
    "ContentFormat",
    "AdditionalDataDeclaration",
]
