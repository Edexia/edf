"""Tests for exceptions."""

import pytest

from edf.exceptions import (
    EDFError,
    EDFValidationError,
    EDFStructureError,
    EDFConsistencyError,
)


class TestEDFError:
    """Tests for base EDFError."""

    def test_is_exception(self):
        """EDFError is an Exception."""
        assert issubclass(EDFError, Exception)

    def test_message(self):
        """EDFError stores message."""
        err = EDFError("test message")
        assert str(err) == "test message"


class TestEDFValidationError:
    """Tests for EDFValidationError."""

    def test_inherits_from_edf_error(self):
        """EDFValidationError inherits from EDFError."""
        assert issubclass(EDFValidationError, EDFError)

    def test_stores_errors_list(self):
        """EDFValidationError stores errors list."""
        errors = ["error 1", "error 2", "error 3"]
        err = EDFValidationError("validation failed", errors=errors)
        assert err.errors == errors

    def test_default_errors_empty(self):
        """EDFValidationError defaults to empty errors list."""
        err = EDFValidationError("validation failed")
        assert err.errors == []

    def test_message(self):
        """EDFValidationError has message."""
        err = EDFValidationError("validation failed", errors=["e1"])
        assert "validation failed" in str(err)


class TestEDFStructureError:
    """Tests for EDFStructureError."""

    def test_inherits_from_edf_error(self):
        """EDFStructureError inherits from EDFError."""
        assert issubclass(EDFStructureError, EDFError)

    def test_message(self):
        """EDFStructureError stores message."""
        err = EDFStructureError("missing file")
        assert str(err) == "missing file"


class TestEDFConsistencyError:
    """Tests for EDFConsistencyError."""

    def test_inherits_from_edf_error(self):
        """EDFConsistencyError inherits from EDFError."""
        assert issubclass(EDFConsistencyError, EDFError)

    def test_message(self):
        """EDFConsistencyError stores message."""
        err = EDFConsistencyError("id mismatch")
        assert str(err) == "id mismatch"


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_catch_all_with_edf_error(self):
        """All EDF exceptions can be caught with EDFError."""
        for exc_class in [EDFValidationError, EDFStructureError, EDFConsistencyError]:
            try:
                raise exc_class("test")
            except EDFError:
                pass  # Should be caught

    def test_specific_catch(self):
        """Specific exceptions can be caught separately."""
        with pytest.raises(EDFValidationError):
            raise EDFValidationError("test")

        with pytest.raises(EDFStructureError):
            raise EDFStructureError("test")

        with pytest.raises(EDFConsistencyError):
            raise EDFConsistencyError("test")
