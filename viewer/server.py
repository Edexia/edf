"""HTTP server with range request support for the EDF viewer."""

import mimetypes
import os
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import BinaryIO


class RangeRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler with support for Range requests (partial content)."""

    edf_file_path: Path | None = None
    static_dir: Path | None = None

    def __init__(self, *args, **kwargs):
        # Set the directory to serve static files from
        if self.static_dir:
            kwargs["directory"] = str(self.static_dir)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests with range support."""
        # Route /file.edf to the actual EDF file
        if self.path == "/file.edf":
            self.serve_edf_file()
            return

        # For other paths, use the default handler
        super().do_GET()

    def serve_edf_file(self):
        """Serve the EDF file with range request support."""
        if not self.edf_file_path or not self.edf_file_path.exists():
            self.send_error(404, "EDF file not found")
            return

        file_size = self.edf_file_path.stat().st_size

        # Check for Range header
        range_header = self.headers.get("Range")
        if range_header:
            self.serve_partial_content(file_size)
        else:
            self.serve_full_content(file_size)

    def serve_full_content(self, file_size: int):
        """Serve the entire file."""
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        with open(self.edf_file_path, "rb") as f:
            self.copyfile(f, self.wfile)

    def serve_partial_content(self, file_size: int):
        """Serve partial content for range requests."""
        range_header = self.headers.get("Range", "")

        # Parse Range header: bytes=start-end
        if not range_header.startswith("bytes="):
            self.send_error(416, "Invalid Range header")
            return

        range_spec = range_header[6:]  # Remove "bytes="

        # Handle multiple ranges (we only support single range)
        if "," in range_spec:
            self.send_error(416, "Multiple ranges not supported")
            return

        # Parse start-end
        parts = range_spec.split("-")
        if len(parts) != 2:
            self.send_error(416, "Invalid Range format")
            return

        start_str, end_str = parts

        # Calculate start and end
        if start_str == "":
            # Suffix range: -500 means last 500 bytes
            suffix_length = int(end_str)
            start = max(0, file_size - suffix_length)
            end = file_size - 1
        elif end_str == "":
            # Range from start to end: 500- means from byte 500 to end
            start = int(start_str)
            end = file_size - 1
        else:
            start = int(start_str)
            end = int(end_str)

        # Validate range
        if start > end or start >= file_size:
            self.send_error(416, "Range Not Satisfiable")
            return

        # Clamp end to file size
        end = min(end, file_size - 1)
        content_length = end - start + 1

        # Send partial content response
        self.send_response(206)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Length", str(content_length))
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Send the requested range
        with open(self.edf_file_path, "rb") as f:
            f.seek(start)
            remaining = content_length
            chunk_size = 8192
            while remaining > 0:
                chunk = f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def do_HEAD(self):
        """Handle HEAD requests."""
        if self.path == "/file.edf":
            if not self.edf_file_path or not self.edf_file_path.exists():
                self.send_error(404, "EDF file not found")
                return

            file_size = self.edf_file_path.stat().st_size
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        else:
            super().do_HEAD()

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Range")
        self.end_headers()

    def log_message(self, format, *args):
        """Override to provide cleaner logging."""
        # Only log non-200 responses and avoid cluttering output
        if len(args) >= 2 and "200" not in str(args[1]) and "206" not in str(args[1]):
            super().log_message(format, *args)


def run_viewer(edf_path: Path, port: int = 8080, open_browser: bool = True):
    """
    Run the EDF viewer server.

    Args:
        edf_path: Path to the EDF file to view
        port: Port to serve on
        open_browser: Whether to automatically open the browser
    """
    # Get the static directory (relative to this file)
    static_dir = Path(__file__).parent / "static"

    if not static_dir.exists():
        raise RuntimeError(f"Static directory not found: {static_dir}")

    # Create a custom handler class with the file paths
    class Handler(RangeRequestHandler):
        pass

    Handler.edf_file_path = edf_path
    Handler.static_dir = static_dir

    server = HTTPServer(("", port), Handler)

    if open_browser:
        webbrowser.open(f"http://localhost:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
