# edf view

> **Navigation**: [CLI](README.md) | [info](info.md) | [validate](validate.md)

Start an interactive web viewer for an EDF file.

## Usage

```bash
edf view <file> [--port PORT] [--no-browser]
```

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--port` | `-p` | 8080 | Port to serve on |
| `--no-browser` | | | Don't open browser automatically |

## Example

```bash
$ edf view assignment.edf
Starting EDF viewer for: /path/to/assignment.edf
Open http://localhost:8080 in your browser
Press Ctrl+C to stop
```

## Port Handling

If the requested port is in use, the viewer finds the next available:

```bash
$ edf view assignment.edf -p 8080
Starting EDF viewer for: /path/to/assignment.edf
Port 8080 in use, using port 8081
Open http://localhost:8081 in your browser
Press Ctrl+C to stop
```

Tries up to 100 consecutive ports.

## Viewer Features

- Browse all submissions
- View content (markdown, PDF, or images)
- Visualize grade distributions per submission
- Interactive grade histogram with adjustable bin size
- Inspect metadata and additional data
- Range request support for large files

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Server stopped normally (Ctrl+C) |
| 1 | File not found or server error |

## Troubleshooting

### Port conflicts

```bash
# Find what's using the port
lsof -i :8080

# Kill if needed
kill <PID>
```

### Large files

The viewer uses HTTP range requests for efficient loading. For very large files (>1GB):
- Use `edf info` for quick inspection
- Run locally rather than over network

## Limitations

- Does not support unzipped directories
- Requires a browser with JavaScript enabled
