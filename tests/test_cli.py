"""Tests for CLI commands."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

from edf.cli import main, cmd_info, cmd_validate, cmd_view


class MockArgs:
    """Mock argparse namespace."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestCmdInfo:
    """Tests for the info command."""

    def test_info_valid_file(self, saved_edf, capsys):
        """Info command on valid file."""
        args = MockArgs(file=str(saved_edf))
        result = cmd_info(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "EDF Version:" in captured.out
        assert "Task ID:" in captured.out
        assert "Max Grade:" in captured.out
        assert "Submissions:" in captured.out

    def test_info_file_not_found(self, tmp_path, capsys):
        """Info command with nonexistent file."""
        args = MockArgs(file=str(tmp_path / "nonexistent.edf"))
        result = cmd_info(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_info_shows_task_attrs(self, saved_edf, capsys):
        """Info shows task additional data attributes."""
        args = MockArgs(file=str(saved_edf))
        cmd_info(args)

        captured = capsys.readouterr()
        assert "Task Attrs:" in captured.out

    def test_info_shows_submission_attrs(self, saved_edf, capsys):
        """Info shows submission additional data attributes."""
        args = MockArgs(file=str(saved_edf))
        cmd_info(args)

        captured = capsys.readouterr()
        assert "Sub Attrs:" in captured.out


class TestCmdValidate:
    """Tests for the validate command."""

    def test_validate_valid_file(self, saved_edf, capsys):
        """Validate command on valid file."""
        args = MockArgs(file=str(saved_edf))
        result = cmd_validate(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "Valid:" in captured.out

    def test_validate_file_not_found(self, tmp_path, capsys):
        """Validate command with nonexistent file."""
        args = MockArgs(file=str(tmp_path / "nonexistent.edf"))
        result = cmd_validate(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_validate_invalid_file(self, tmp_path, capsys):
        """Validate command on invalid file."""
        # Create an invalid EDF (empty zip)
        invalid_path = tmp_path / "invalid.edf"
        import zipfile
        with zipfile.ZipFile(invalid_path, "w") as zf:
            zf.writestr("random.txt", "not an edf")

        args = MockArgs(file=str(invalid_path))
        result = cmd_validate(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "Invalid:" in captured.err or "Error:" in captured.err


class TestCmdView:
    """Tests for the view command."""

    def test_view_file_not_found(self, tmp_path, capsys):
        """View command with nonexistent file."""
        args = MockArgs(
            file=str(tmp_path / "nonexistent.edf"),
            port=8080,
            no_browser=True,
        )
        result = cmd_view(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()

    def test_view_starts_server(self, saved_edf, capsys):
        """View command starts server (mocked)."""
        args = MockArgs(
            file=str(saved_edf),
            port=9999,
            no_browser=True,
        )

        with patch("viewer.server.run_viewer") as mock_run:
            mock_run.side_effect = KeyboardInterrupt()
            result = cmd_view(args)

            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args
            assert call_kwargs[1]["port"] == 9999
            assert call_kwargs[1]["open_browser"] is False
            assert call_kwargs[1]["on_ready"] is not None

    def test_view_shows_port_change_message(self, saved_edf, capsys):
        """View command shows message when port changes."""
        args = MockArgs(
            file=str(saved_edf),
            port=8080,
            no_browser=True,
        )

        def run_viewer_mock(path, port, open_browser, on_ready):
            # Simulate port change from 8080 to 8081
            on_ready(8081)
            raise KeyboardInterrupt()

        with patch("viewer.server.run_viewer", side_effect=run_viewer_mock):
            result = cmd_view(args)

        captured = capsys.readouterr()
        assert "Port 8080 in use" in captured.out
        assert "using port 8081" in captured.out
        assert "http://localhost:8081" in captured.out

    def test_view_no_port_change_message_when_same(self, saved_edf, capsys):
        """View command doesn't show port change message when port is same."""
        args = MockArgs(
            file=str(saved_edf),
            port=8080,
            no_browser=True,
        )

        def run_viewer_mock(path, port, open_browser, on_ready):
            # Port stays the same
            on_ready(8080)
            raise KeyboardInterrupt()

        with patch("viewer.server.run_viewer", side_effect=run_viewer_mock):
            result = cmd_view(args)

        captured = capsys.readouterr()
        assert "Port 8080 in use" not in captured.out
        assert "http://localhost:8080" in captured.out


class TestCmdInfoEdgeCases:
    """Edge case tests for the info command."""

    def test_info_without_task_attrs(self, tmp_path, capsys):
        """Info command when EDF has no task additional data."""
        from edf import EDF
        from tests.conftest import make_distribution

        edf = EDF(max_grade=10)
        # No set_task_data() call - empty task_data
        edf.add_submission(
            submission_id="student1",
            grade=5,
            optimistic=make_distribution(6, 10),
            expected=make_distribution(5, 10),
            pessimistic=make_distribution(4, 10),
            content="Test content",
        )
        path = tmp_path / "no_task_attrs.edf"
        edf.save(path)

        args = MockArgs(file=str(path))
        result = cmd_info(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "Task Attrs:" not in captured.out

    def test_info_without_submission_attrs(self, tmp_path, capsys):
        """Info command when EDF has no submission additional data."""
        from edf import EDF
        from tests.conftest import make_distribution

        edf = EDF(max_grade=10)
        edf.set_task_data(school_id="TEST")
        edf.add_submission(
            submission_id="student1",
            grade=5,
            optimistic=make_distribution(6, 10),
            expected=make_distribution(5, 10),
            pessimistic=make_distribution(4, 10),
            content="Test content",
            # No additional submission attributes
        )
        path = tmp_path / "no_sub_attrs.edf"
        edf.save(path)

        args = MockArgs(file=str(path))
        result = cmd_info(args)
        assert result == 0

        captured = capsys.readouterr()
        assert "Sub Attrs:" not in captured.out
        assert "Task Attrs:" in captured.out

    def test_info_corrupt_file(self, tmp_path, capsys):
        """Info command with a corrupt/unreadable EDF file."""
        corrupt_path = tmp_path / "corrupt.edf"
        corrupt_path.write_bytes(b"not a zip file")

        args = MockArgs(file=str(corrupt_path))
        result = cmd_info(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err


class TestCmdValidateEdgeCases:
    """Edge case tests for the validate command."""

    def test_validate_corrupt_file(self, tmp_path, capsys):
        """Validate command with corrupt file (non-EDFValidationError)."""
        corrupt_path = tmp_path / "corrupt.edf"
        corrupt_path.write_bytes(b"not a zip file")

        args = MockArgs(file=str(corrupt_path))
        result = cmd_validate(args)
        assert result == 1

        captured = capsys.readouterr()
        assert "Error:" in captured.err


class TestMainEntrypoint:
    """Tests for main() entrypoint."""

    def test_main_info(self, saved_edf):
        """Main with info subcommand."""
        with patch.object(sys, "argv", ["edf", "info", str(saved_edf)]):
            result = main()
            assert result == 0

    def test_main_validate(self, saved_edf):
        """Main with validate subcommand."""
        with patch.object(sys, "argv", ["edf", "validate", str(saved_edf)]):
            result = main()
            assert result == 0

    def test_main_no_command(self, capsys):
        """Main with no subcommand shows error."""
        with patch.object(sys, "argv", ["edf"]):
            with pytest.raises(SystemExit):
                main()

    def test_main_view(self, saved_edf):
        """Main with view subcommand."""
        with patch.object(sys, "argv", ["edf", "view", str(saved_edf), "--no-browser"]):
            with patch("viewer.server.run_viewer") as mock_run:
                mock_run.side_effect = KeyboardInterrupt()
                result = main()
                assert result == 0
