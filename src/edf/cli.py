"""Command-line interface for EDF tools."""

import argparse
import sys
from pathlib import Path

from edf.reader import EDFReader
from edf.exceptions import EDFValidationError


def cmd_info(args: argparse.Namespace) -> int:
    """Show summary information about an EDF file."""
    path = Path(args.file)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        with EDFReader.open(path, validate=False) as reader:
            m = reader.manifest
            t = reader.task.core

            print(f"EDF Version:    {m.edf_version}")
            print(f"Task ID:        {m.task_id}")
            print(f"Version:        {t.version}")
            print(f"Content Hash:   {m.content_hash[:20]}...")
            print(f"Created:        {m.created_at}")
            print(f"Content Format: {m.content_format.value}")
            print(f"Max Grade:      {t.max_grade}")
            print(f"Submissions:    {m.submission_count}")
            print(f"Has Rubric:     {m.has_rubric}")
            print(f"Has Prompt:     {m.has_prompt}")

            if m.additional_data.task:
                print(f"Task Attrs:     {', '.join(m.additional_data.task)}")
            if m.additional_data.submission:
                print(f"Sub Attrs:      {', '.join(m.additional_data.submission)}")

    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate an EDF file and report any errors."""
    path = Path(args.file)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        with EDFReader.open(path, validate=True) as reader:
            # If we get here, validation passed
            print(f"Valid: {path}")
            print(f"  Task ID: {reader.manifest.task_id}")
            print(f"  Submissions: {reader.manifest.submission_count}")
            return 0
    except EDFValidationError as e:
        print(f"Invalid: {path}", file=sys.stderr)
        for error in e.errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_view(args: argparse.Namespace) -> int:
    """Start a web viewer for an EDF file."""
    path = Path(args.file).resolve()
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    port = args.port

    # Import here to avoid loading viewer deps when not needed
    from viewer.server import run_viewer

    print(f"Starting EDF viewer for: {path}")
    print(f"Open http://localhost:{port} in your browser")
    print("Press Ctrl+C to stop")

    try:
        run_viewer(path, port=port, open_browser=not args.no_browser)
    except KeyboardInterrupt:
        print("\nStopped")

    return 0


def main() -> int:
    """Main entry point for the EDF CLI."""
    parser = argparse.ArgumentParser(
        prog="edf",
        description="Tools for working with Edexia Data Format (.edf) files",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # info command
    info_parser = subparsers.add_parser(
        "info", help="Show summary information about an EDF file"
    )
    info_parser.add_argument("file", help="Path to the .edf file")

    # validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate an EDF file and report any errors"
    )
    validate_parser.add_argument("file", help="Path to the .edf file")

    # view command
    view_parser = subparsers.add_parser(
        "view", help="Start a web viewer for an EDF file"
    )
    view_parser.add_argument("file", help="Path to the .edf file")
    view_parser.add_argument(
        "--port", "-p", type=int, default=8080, help="Port to serve on (default: 8080)"
    )
    view_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open the browser",
    )

    args = parser.parse_args()

    if args.command == "info":
        return cmd_info(args)
    elif args.command == "validate":
        return cmd_validate(args)
    elif args.command == "view":
        return cmd_view(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
