"""Command-line interface for EDF tools."""

import argparse
import sys
from pathlib import Path

from edf.core import EDF
from edf.exceptions import EDFValidationError


def cmd_info(args: argparse.Namespace) -> int:
    """Show summary information about an EDF file."""
    path = Path(args.file)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    try:
        with EDF.open(path, validate=False) as edf:
            print(f"EDF Version:    {edf.edf_version}")
            print(f"Task ID:        {edf.task_id}")
            print(f"Version:        {edf.version}")
            print(f"Content Hash:   {edf.content_hash[:20]}..." if edf.content_hash else "Content Hash:   N/A")
            print(f"Created:        {edf.created_at}")
            print(f"Content Format: {edf.content_format.value if edf.content_format else 'N/A'}")
            print(f"Max Grade:      {edf.max_grade}")
            print(f"Submissions:    {len(edf.submissions)}")
            print(f"Has Rubric:     {edf.rubric is not None}")
            print(f"Has Prompt:     {edf.prompt is not None}")

            if edf.task_data:
                print(f"Task Attrs:     {', '.join(edf.task_data.keys())}")

            sub_attrs: set[str] = set()
            for sub in edf.submissions:
                sub_attrs.update(sub.additional.keys())
            if sub_attrs:
                print(f"Sub Attrs:      {', '.join(sorted(sub_attrs))}")

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
        with EDF.open(path, validate=True) as edf:
            print(f"Valid: {path}")
            print(f"  Task ID: {edf.task_id}")
            print(f"  Submissions: {len(edf.submissions)}")
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
