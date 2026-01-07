"""Tests for the viewer server module."""

import base64
import io
import json
import socket
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

from edf import EDF
from viewer.server import find_available_port, run_viewer, RangeRequestHandler


class TestFindAvailablePort:
    """Tests for find_available_port function."""

    def test_finds_available_port(self):
        """Should return the starting port if available."""
        # Use a high port that's likely available
        port = find_available_port(59123)
        assert port >= 59123
        assert port < 59123 + 100

    def test_skips_occupied_port(self):
        """Should skip to next port if requested port is in use."""
        # Bind to a port to occupy it
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 59234))
            s.listen(1)
            # Now try to find a port starting from the occupied one
            port = find_available_port(59234)
            assert port == 59235

    def test_raises_when_no_port_available(self):
        """Should raise RuntimeError when no port found within max_attempts."""
        # Mock socket.bind to always fail
        with patch("socket.socket") as mock_socket:
            mock_sock_instance = MagicMock()
            mock_sock_instance.__enter__ = MagicMock(return_value=mock_sock_instance)
            mock_sock_instance.__exit__ = MagicMock(return_value=False)
            mock_sock_instance.bind.side_effect = OSError("Address in use")
            mock_socket.return_value = mock_sock_instance

            with pytest.raises(RuntimeError) as exc_info:
                find_available_port(8080, max_attempts=3)

            assert "Could not find an available port" in str(exc_info.value)
            assert "3 attempts" in str(exc_info.value)


class TestRunViewer:
    """Tests for run_viewer function."""

    def test_on_ready_callback_called(self, saved_edf):
        """on_ready callback should be called with actual port."""
        callback_port = None

        def on_ready(port: int):
            nonlocal callback_port
            callback_port = port

        with patch("viewer.server.ThreadingHTTPServer") as mock_server_class:
            mock_server = MagicMock()
            mock_server.serve_forever.side_effect = KeyboardInterrupt()
            mock_server_class.return_value = mock_server

            with patch("viewer.server.find_available_port", return_value=9999):
                run_viewer(saved_edf, port=8080, open_browser=False, on_ready=on_ready)

            assert callback_port == 9999

    def test_on_ready_not_called_when_none(self, saved_edf):
        """Should not error when on_ready is None."""
        with patch("viewer.server.ThreadingHTTPServer") as mock_server_class:
            mock_server = MagicMock()
            mock_server.serve_forever.side_effect = KeyboardInterrupt()
            mock_server_class.return_value = mock_server

            with patch("viewer.server.find_available_port", return_value=8080):
                # Should not raise
                result = run_viewer(
                    saved_edf, port=8080, open_browser=False, on_ready=None
                )
                assert result == 8080

    def test_returns_actual_port(self, saved_edf):
        """Should return the actual port used."""
        with patch("viewer.server.ThreadingHTTPServer") as mock_server_class:
            mock_server = MagicMock()
            mock_server.serve_forever.side_effect = KeyboardInterrupt()
            mock_server_class.return_value = mock_server

            with patch("viewer.server.find_available_port", return_value=9876):
                result = run_viewer(saved_edf, port=8080, open_browser=False)
                assert result == 9876

    def test_opens_browser_when_requested(self, saved_edf):
        """Should open browser when open_browser=True."""
        with patch("viewer.server.ThreadingHTTPServer") as mock_server_class:
            mock_server = MagicMock()
            mock_server.serve_forever.side_effect = KeyboardInterrupt()
            mock_server_class.return_value = mock_server

            with patch("viewer.server.find_available_port", return_value=8080):
                with patch("viewer.server.webbrowser.open") as mock_open:
                    run_viewer(saved_edf, port=8080, open_browser=True)
                    mock_open.assert_called_once_with("http://localhost:8080")

    def test_no_browser_when_disabled(self, saved_edf):
        """Should not open browser when open_browser=False."""
        with patch("viewer.server.ThreadingHTTPServer") as mock_server_class:
            mock_server = MagicMock()
            mock_server.serve_forever.side_effect = KeyboardInterrupt()
            mock_server_class.return_value = mock_server

            with patch("viewer.server.find_available_port", return_value=8080):
                with patch("viewer.server.webbrowser.open") as mock_open:
                    run_viewer(saved_edf, port=8080, open_browser=False)
                    mock_open.assert_not_called()

    def test_static_dir_not_found(self, saved_edf, tmp_path):
        """Should raise RuntimeError if static directory doesn't exist."""
        import viewer.server as server_module

        # Get the real static_dir path calculation logic
        fake_static = tmp_path / "nonexistent_static"

        # Mock Path(__file__).parent / "static" to return a non-existent path
        original_func = server_module.run_viewer

        def patched_run_viewer(edf_path, port=8080, open_browser=True, on_ready=None):
            # Temporarily replace the static_dir calculation
            with patch.object(server_module, "Path") as mock_path:
                mock_file_path = MagicMock()
                mock_parent = MagicMock()
                mock_static_dir = MagicMock()
                mock_static_dir.exists.return_value = False
                mock_static_dir.__str__ = MagicMock(return_value=str(fake_static))
                mock_parent.__truediv__ = MagicMock(return_value=mock_static_dir)
                mock_file_path.parent = mock_parent
                mock_path.return_value = mock_file_path

                # Call the original function which should raise
                return original_func(edf_path, port, open_browser, on_ready)

        # The simplest approach: directly test with mocked exists()
        with patch("viewer.server.Path") as mock_path_class:
            # Set up the chain: Path(__file__).parent / "static"
            mock_static = MagicMock()
            mock_static.exists.return_value = False

            mock_parent = MagicMock()
            mock_parent.__truediv__.return_value = mock_static

            mock_file = MagicMock()
            mock_file.parent = mock_parent

            mock_path_class.return_value = mock_file

            with pytest.raises(RuntimeError) as exc_info:
                run_viewer(saved_edf, port=8080, open_browser=False)

            assert "Static directory not found" in str(exc_info.value)

    def test_server_close_called_on_interrupt(self, saved_edf):
        """Server should be closed after KeyboardInterrupt."""
        with patch("viewer.server.ThreadingHTTPServer") as mock_server_class:
            mock_server = MagicMock()
            mock_server.serve_forever.side_effect = KeyboardInterrupt()
            mock_server_class.return_value = mock_server

            with patch("viewer.server.find_available_port", return_value=8080):
                run_viewer(saved_edf, port=8080, open_browser=False)
                mock_server.server_close.assert_called_once()


class TestRangeRequestHandler:
    """Tests for RangeRequestHandler class."""

    def _create_handler(self, edf_path=None, static_dir=None, path="/", headers=None):
        """Create a mock handler for testing."""
        # Create a subclass with the class variables set
        class TestHandler(RangeRequestHandler):
            pass

        TestHandler.edf_file_path = edf_path
        TestHandler.static_dir = static_dir

        # Create mock request, client_address, and server
        mock_request = MagicMock()
        mock_request.makefile.return_value = io.BytesIO()
        mock_client_address = ("127.0.0.1", 12345)
        mock_server = MagicMock()

        # Patch the handler's __init__ to avoid actual socket operations
        with patch.object(RangeRequestHandler, "__init__", lambda self, *args, **kwargs: None):
            handler = TestHandler(mock_request, mock_client_address, mock_server)

        # Set up the handler's attributes
        handler.path = path
        handler.headers = headers or {}
        handler.wfile = io.BytesIO()
        handler.requestline = f"GET {path} HTTP/1.1"
        handler.request_version = "HTTP/1.1"
        handler.command = "GET"

        # Mock send methods
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.send_error = MagicMock()
        handler.copyfile = MagicMock()

        return handler

    def test_do_get_edf_file(self, saved_edf, tmp_path):
        """GET /file.edf should serve the EDF file."""
        handler = self._create_handler(edf_path=saved_edf, path="/file.edf")

        # Mock serve_edf_file
        handler.serve_edf_file = MagicMock()
        handler.do_GET()

        handler.serve_edf_file.assert_called_once()

    def test_do_get_other_path(self, tmp_path):
        """GET other paths should use default handler."""
        handler = self._create_handler(path="/index.html")

        with patch.object(RangeRequestHandler.__bases__[0], "do_GET") as mock_super:
            handler.do_GET()
            mock_super.assert_called_once()

    def test_serve_edf_file_not_found(self, tmp_path):
        """serve_edf_file with missing file returns 404."""
        handler = self._create_handler(edf_path=tmp_path / "nonexistent.edf")
        handler.serve_edf_file()
        handler.send_error.assert_called_with(404, "EDF file not found")

    def test_serve_edf_file_none_path(self):
        """serve_edf_file with None path returns 404."""
        handler = self._create_handler(edf_path=None)
        handler.serve_edf_file()
        handler.send_error.assert_called_with(404, "EDF file not found")

    def test_serve_edf_file_full_content(self, saved_edf):
        """serve_edf_file without Range header serves full content."""
        handler = self._create_handler(edf_path=saved_edf, headers={})
        handler.headers = MagicMock()
        handler.headers.get.return_value = None

        handler.serve_full_content = MagicMock()
        handler.serve_edf_file()

        handler.serve_full_content.assert_called_once()

    def test_serve_edf_file_partial_content(self, saved_edf):
        """serve_edf_file with Range header serves partial content."""
        handler = self._create_handler(edf_path=saved_edf)
        handler.headers = MagicMock()
        handler.headers.get.return_value = "bytes=0-100"

        handler.serve_partial_content = MagicMock()
        handler.serve_edf_file()

        handler.serve_partial_content.assert_called_once()

    def test_serve_full_content(self, saved_edf):
        """serve_full_content sends correct headers and content."""
        handler = self._create_handler(edf_path=saved_edf)
        file_size = saved_edf.stat().st_size

        handler.serve_full_content(file_size)

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call("Content-Type", "application/zip")
        handler.send_header.assert_any_call("Content-Length", str(file_size))
        handler.send_header.assert_any_call("Accept-Ranges", "bytes")
        handler.send_header.assert_any_call("Access-Control-Allow-Origin", "*")
        handler.end_headers.assert_called_once()
        handler.copyfile.assert_called_once()

    def test_serve_partial_content_invalid_header(self, saved_edf):
        """serve_partial_content with invalid Range header sends 416."""
        handler = self._create_handler(edf_path=saved_edf)
        handler.headers = MagicMock()
        handler.headers.get.return_value = "invalid=0-100"

        handler.serve_partial_content(1000)

        handler.send_error.assert_called_with(416, "Invalid Range header")

    def test_serve_partial_content_multiple_ranges(self, saved_edf):
        """serve_partial_content with multiple ranges sends 416."""
        handler = self._create_handler(edf_path=saved_edf)
        handler.headers = MagicMock()
        handler.headers.get.return_value = "bytes=0-100,200-300"

        handler.serve_partial_content(1000)

        handler.send_error.assert_called_with(416, "Multiple ranges not supported")

    def test_serve_partial_content_invalid_format(self, saved_edf):
        """serve_partial_content with invalid format sends 416."""
        handler = self._create_handler(edf_path=saved_edf)
        handler.headers = MagicMock()
        handler.headers.get.return_value = "bytes=invalid"

        handler.serve_partial_content(1000)

        handler.send_error.assert_called_with(416, "Invalid Range format")

    def test_serve_partial_content_suffix_range(self, saved_edf):
        """serve_partial_content handles suffix range (-500)."""
        handler = self._create_handler(edf_path=saved_edf)
        handler.headers = MagicMock()
        handler.headers.get.return_value = "bytes=-100"

        file_size = saved_edf.stat().st_size
        handler.serve_partial_content(file_size)

        handler.send_response.assert_called_with(206)

    def test_serve_partial_content_open_ended_range(self, saved_edf):
        """serve_partial_content handles open-ended range (500-)."""
        handler = self._create_handler(edf_path=saved_edf)
        handler.headers = MagicMock()
        handler.headers.get.return_value = "bytes=0-"

        file_size = saved_edf.stat().st_size
        handler.serve_partial_content(file_size)

        handler.send_response.assert_called_with(206)

    def test_serve_partial_content_full_range(self, saved_edf):
        """serve_partial_content handles full range (0-100)."""
        handler = self._create_handler(edf_path=saved_edf)
        handler.headers = MagicMock()
        handler.headers.get.return_value = "bytes=0-100"

        file_size = saved_edf.stat().st_size
        handler.serve_partial_content(file_size)

        handler.send_response.assert_called_with(206)
        handler.send_header.assert_any_call("Content-Type", "application/zip")

    def test_serve_partial_content_unsatisfiable_range(self, saved_edf):
        """serve_partial_content with out-of-range sends 416."""
        handler = self._create_handler(edf_path=saved_edf)
        handler.headers = MagicMock()
        handler.headers.get.return_value = "bytes=999999-1000000"

        file_size = 100  # Small file
        handler.serve_partial_content(file_size)

        handler.send_error.assert_called_with(416, "Range Not Satisfiable")

    def test_serve_partial_content_start_greater_than_end(self, saved_edf):
        """serve_partial_content with start > end sends 416."""
        handler = self._create_handler(edf_path=saved_edf)
        handler.headers = MagicMock()
        handler.headers.get.return_value = "bytes=100-50"

        file_size = 1000
        handler.serve_partial_content(file_size)

        handler.send_error.assert_called_with(416, "Range Not Satisfiable")

    def test_serve_partial_content_early_eof(self, saved_edf):
        """serve_partial_content handles early EOF during read."""
        handler = self._create_handler(edf_path=saved_edf)
        handler.headers = MagicMock()
        handler.headers.get.return_value = "bytes=0-100"

        # Create a mock file that returns empty on second read
        mock_file = MagicMock()
        mock_file.read.side_effect = [b"some data", b""]  # Second read returns empty
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)

        file_size = saved_edf.stat().st_size

        with patch("builtins.open", return_value=mock_file):
            handler.serve_partial_content(file_size)

        # Should still send 206 response
        handler.send_response.assert_called_with(206)
        # File read should have been called at least once
        assert mock_file.read.call_count >= 1

    def test_do_head_edf_file(self, saved_edf):
        """HEAD /file.edf returns file info without body."""
        handler = self._create_handler(edf_path=saved_edf, path="/file.edf")
        file_size = saved_edf.stat().st_size

        handler.do_HEAD()

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call("Content-Length", str(file_size))

    def test_do_head_edf_file_not_found(self, tmp_path):
        """HEAD /file.edf with missing file returns 404."""
        handler = self._create_handler(edf_path=tmp_path / "nonexistent.edf", path="/file.edf")
        handler.do_HEAD()
        handler.send_error.assert_called_with(404, "EDF file not found")

    def test_do_head_edf_file_none_path(self):
        """HEAD /file.edf with None path returns 404."""
        handler = self._create_handler(edf_path=None, path="/file.edf")
        handler.do_HEAD()
        handler.send_error.assert_called_with(404, "EDF file not found")

    def test_do_head_other_path(self):
        """HEAD other paths should use default handler."""
        handler = self._create_handler(path="/index.html")

        with patch.object(RangeRequestHandler.__bases__[0], "do_HEAD") as mock_super:
            handler.do_HEAD()
            mock_super.assert_called_once()

    def test_do_options(self):
        """OPTIONS request returns CORS headers."""
        handler = self._create_handler(path="/file.edf")
        handler.do_OPTIONS()

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call("Access-Control-Allow-Origin", "*")
        handler.send_header.assert_any_call("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        handler.send_header.assert_any_call("Access-Control-Allow-Headers", "Range")
        handler.end_headers.assert_called_once()

    def test_log_message_non_200(self):
        """log_message logs non-200 responses."""
        handler = self._create_handler()

        with patch.object(RangeRequestHandler.__bases__[0], "log_message") as mock_super:
            handler.log_message("%s", "request", "404")
            mock_super.assert_called_once()

    def test_log_message_200(self):
        """log_message suppresses 200 responses."""
        handler = self._create_handler()

        with patch.object(RangeRequestHandler.__bases__[0], "log_message") as mock_super:
            handler.log_message("%s", "request", "200")
            mock_super.assert_not_called()

    def test_log_message_206(self):
        """log_message suppresses 206 responses."""
        handler = self._create_handler()

        with patch.object(RangeRequestHandler.__bases__[0], "log_message") as mock_super:
            handler.log_message("%s", "request", "206")
            mock_super.assert_not_called()

    def test_log_message_insufficient_args(self):
        """log_message with insufficient args doesn't log."""
        handler = self._create_handler()

        with patch.object(RangeRequestHandler.__bases__[0], "log_message") as mock_super:
            handler.log_message("%s")
            mock_super.assert_not_called()

    def test_init_with_static_dir(self, tmp_path):
        """Handler __init__ sets directory when static_dir is set."""
        static_dir = tmp_path / "static"
        static_dir.mkdir()

        class TestHandler(RangeRequestHandler):
            pass

        TestHandler.static_dir = static_dir

        # Mock the request objects
        mock_request = MagicMock()
        mock_request.makefile.return_value = io.BytesIO(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")

        with patch.object(RangeRequestHandler.__bases__[0], "__init__") as mock_super_init:
            mock_super_init.return_value = None
            handler = TestHandler(mock_request, ("127.0.0.1", 12345), MagicMock())
            mock_super_init.assert_called_once()
            # Check that directory was passed
            call_kwargs = mock_super_init.call_args[1]
            assert call_kwargs.get("directory") == str(static_dir)

    def test_init_without_static_dir(self):
        """Handler __init__ works without static_dir."""
        class TestHandler(RangeRequestHandler):
            pass

        TestHandler.static_dir = None

        mock_request = MagicMock()
        mock_request.makefile.return_value = io.BytesIO(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")

        with patch.object(RangeRequestHandler.__bases__[0], "__init__") as mock_super_init:
            mock_super_init.return_value = None
            handler = TestHandler(mock_request, ("127.0.0.1", 12345), MagicMock())
            mock_super_init.assert_called_once()
            # Check that directory was NOT passed
            call_kwargs = mock_super_init.call_args[1]
            assert "directory" not in call_kwargs


class TestAPIEndpoints:
    """Tests for REST API endpoints."""

    def _create_handler_with_edf(self, edf_path, path="/", headers=None):
        """Create a mock handler with an EDF instance loaded."""
        edf = EDF.open(edf_path)

        class TestHandler(RangeRequestHandler):
            pass

        TestHandler.edf_file_path = edf_path
        TestHandler.static_dir = None
        TestHandler.edf_instance = edf

        mock_request = MagicMock()
        mock_request.makefile.return_value = io.BytesIO()
        mock_client_address = ("127.0.0.1", 12345)
        mock_server = MagicMock()

        with patch.object(RangeRequestHandler, "__init__", lambda self, *args, **kwargs: None):
            handler = TestHandler(mock_request, mock_client_address, mock_server)

        handler.path = path
        handler.headers = headers or {}
        handler.wfile = io.BytesIO()
        handler.requestline = f"GET {path} HTTP/1.1"
        handler.request_version = "HTTP/1.1"
        handler.command = "GET"

        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.send_error = MagicMock()
        handler.copyfile = MagicMock()

        return handler

    def _create_handler_without_edf(self, path="/"):
        """Create a mock handler without an EDF instance."""
        class TestHandler(RangeRequestHandler):
            pass

        TestHandler.edf_file_path = None
        TestHandler.static_dir = None
        TestHandler.edf_instance = None

        mock_request = MagicMock()
        mock_request.makefile.return_value = io.BytesIO()
        mock_client_address = ("127.0.0.1", 12345)
        mock_server = MagicMock()

        with patch.object(RangeRequestHandler, "__init__", lambda self, *args, **kwargs: None):
            handler = TestHandler(mock_request, mock_client_address, mock_server)

        handler.path = path
        handler.headers = {}
        handler.wfile = io.BytesIO()
        handler.requestline = f"GET {path} HTTP/1.1"
        handler.request_version = "HTTP/1.1"
        handler.command = "GET"

        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.send_error = MagicMock()

        return handler

    # Tests for /api/manifest endpoint

    def test_api_manifest_returns_json(self, saved_edf):
        """GET /api/manifest returns manifest, task, rubric, prompt."""
        handler = self._create_handler_with_edf(saved_edf, path="/api/manifest")
        handler.do_GET()

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call("Content-Type", "application/json")
        handler.send_header.assert_any_call("Access-Control-Allow-Origin", "*")

        # Check the JSON response
        response_body = handler.wfile.getvalue().decode("utf-8")
        data = json.loads(response_body)

        assert "manifest" in data
        assert "task" in data
        assert "rubric" in data
        assert "prompt" in data

        # Check manifest fields
        assert "task_id" in data["manifest"]
        assert "edf_version" in data["manifest"]
        assert "content_format" in data["manifest"]
        assert "submission_count" in data["manifest"]
        assert data["manifest"]["submission_count"] == 3

        # Check task fields
        assert "max_grade" in data["task"]
        assert data["task"]["max_grade"] == 20

    def test_api_manifest_without_edf_returns_500(self):
        """GET /api/manifest without EDF loaded returns 500."""
        handler = self._create_handler_without_edf(path="/api/manifest")
        handler.do_GET()

        handler.send_error.assert_called_with(500, "EDF not loaded")

    # Tests for /api/submissions endpoint

    def test_api_submissions_returns_list(self, saved_edf):
        """GET /api/submissions returns submission list without content."""
        handler = self._create_handler_with_edf(saved_edf, path="/api/submissions")
        handler.do_GET()

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call("Content-Type", "application/json")

        response_body = handler.wfile.getvalue().decode("utf-8")
        data = json.loads(response_body)

        assert "submissions" in data
        assert len(data["submissions"]) == 3

        # Check submission structure
        sub = data["submissions"][0]
        assert "id" in sub
        assert "grade" in sub
        assert "distributions" in sub
        assert "additional" in sub

        # Check distributions structure
        assert "optimistic" in sub["distributions"]
        assert "expected" in sub["distributions"]
        assert "pessimistic" in sub["distributions"]

        # Verify content is NOT included
        assert "content" not in sub

    def test_api_submissions_without_edf_returns_500(self):
        """GET /api/submissions without EDF loaded returns 500."""
        handler = self._create_handler_without_edf(path="/api/submissions")
        handler.do_GET()

        handler.send_error.assert_called_with(500, "EDF not loaded")

    # Tests for /api/submissions/{id}/content endpoint

    def test_api_submission_content_markdown(self, saved_edf):
        """GET /api/submissions/{id}/content returns markdown content."""
        handler = self._create_handler_with_edf(
            saved_edf, path="/api/submissions/student_alice/content"
        )
        handler.do_GET()

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call("Content-Type", "application/json")

        response_body = handler.wfile.getvalue().decode("utf-8")
        data = json.loads(response_body)

        assert data["format"] == "markdown"
        assert "content" in data
        assert "alice" in data["content"].lower()

    def test_api_submission_content_pdf(self, saved_pdf_edf):
        """GET /api/submissions/{id}/content returns PDF binary."""
        handler = self._create_handler_with_edf(
            saved_pdf_edf, path="/api/submissions/sub1/content"
        )
        handler.do_GET()

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call("Content-Type", "application/pdf")
        handler.send_header.assert_any_call("Access-Control-Allow-Origin", "*")

        # Check that PDF bytes were written
        response_body = handler.wfile.getvalue()
        assert b"PDF" in response_body

    def test_api_submission_content_images(self, saved_images_edf):
        """GET /api/submissions/{id}/content returns base64 images."""
        handler = self._create_handler_with_edf(
            saved_images_edf, path="/api/submissions/sub1/content"
        )
        handler.do_GET()

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call("Content-Type", "application/json")

        response_body = handler.wfile.getvalue().decode("utf-8")
        data = json.loads(response_body)

        assert data["format"] == "images"
        assert "pages" in data
        assert len(data["pages"]) == 2

        # Verify base64 encoding
        decoded = base64.b64decode(data["pages"][0])
        assert decoded == b"fake jpg 0"

    def test_api_submission_content_not_found(self, saved_edf):
        """GET /api/submissions/{invalid}/content returns 404."""
        handler = self._create_handler_with_edf(
            saved_edf, path="/api/submissions/nonexistent_student/content"
        )
        handler.do_GET()

        handler.send_error.assert_called()
        call_args = handler.send_error.call_args
        assert call_args[0][0] == 404
        assert "nonexistent_student" in call_args[0][1]

    def test_api_submission_content_without_edf_returns_500(self):
        """GET /api/submissions/{id}/content without EDF returns 500."""
        handler = self._create_handler_without_edf(
            path="/api/submissions/test/content"
        )
        handler.do_GET()

        handler.send_error.assert_called_with(500, "EDF not loaded")

    # Tests for routing

    def test_do_get_routes_api_manifest(self, saved_edf):
        """GET /api/manifest should route to serve_api_manifest."""
        handler = self._create_handler_with_edf(saved_edf, path="/api/manifest")
        handler.serve_api_manifest = MagicMock()

        handler.do_GET()

        handler.serve_api_manifest.assert_called_once()

    def test_do_get_routes_api_submissions(self, saved_edf):
        """GET /api/submissions should route to serve_api_submissions."""
        handler = self._create_handler_with_edf(saved_edf, path="/api/submissions")
        handler.serve_api_submissions = MagicMock()

        handler.do_GET()

        handler.serve_api_submissions.assert_called_once()

    def test_do_get_routes_api_submission_content(self, saved_edf):
        """GET /api/submissions/{id}/content should route to serve_api_submission_content."""
        handler = self._create_handler_with_edf(
            saved_edf, path="/api/submissions/test_id/content"
        )
        handler.serve_api_submission_content = MagicMock()

        handler.do_GET()

        handler.serve_api_submission_content.assert_called_once_with("test_id")

    def test_do_get_invalid_api_path_falls_through(self, saved_edf):
        """GET /api/submissions/foo (without /content) should fall through to default."""
        handler = self._create_handler_with_edf(
            saved_edf, path="/api/submissions/foo"
        )

        with patch.object(RangeRequestHandler.__bases__[0], "do_GET") as mock_super:
            handler.do_GET()
            mock_super.assert_called_once()

    # Tests for _send_json helper

    def test_send_json_helper(self, saved_edf):
        """_send_json sends correct headers and body."""
        handler = self._create_handler_with_edf(saved_edf)

        test_data = {"key": "value", "number": 42}
        handler._send_json(test_data)

        handler.send_response.assert_called_with(200)
        handler.send_header.assert_any_call("Content-Type", "application/json")
        handler.send_header.assert_any_call("Access-Control-Allow-Origin", "*")

        response_body = handler.wfile.getvalue().decode("utf-8")
        assert json.loads(response_body) == test_data

    def test_send_json_custom_status(self, saved_edf):
        """_send_json can send custom status codes."""
        handler = self._create_handler_with_edf(saved_edf)

        handler._send_json({"error": "test"}, status=400)

        handler.send_response.assert_called_with(400)
