# Signa

Privacy-preserving threat intelligence. Compute a file SHA-256 hash locally, send only the 64 character hash to a cloud API, and receive a malware verdict from a threat database. No file uploads, no privacy risk.

## Architecture

```
Local File  ->  Chunked SHA-256  ->  FastAPI Lookup  ->  PostgreSQL / SQLite  ->  Verdict
                                                          |
                                                    MalwareBazaar Feed
                                                    (seed script)
```

The system has three layers:

- **CLI** (Typer + Rich) -- For pro users. Hash a file on disk or look up a hash directly. Shows a formatted table with the verdict.
- **API** (FastAPI + SQLAlchemy) -- REST endpoint at `/api/lookup/{sha256}`. Returns JSON with status, family, confidence, source, timestamps.
- **Web UI** (FastAPI + Jinja2) -- For basic users. Two workflows: paste a hash manually, or upload a file (any type) for automatic hashing and lookup. Includes scan history.

Only the SHA-256 hash ever leaves your device. The original file is read in 8 KB chunks, hashed in memory, and discarded.

## Features

- Chunked SHA-256 hashing -- handles multi-gigabyte files with constant memory usage
- Hash lookup against a database of known malware indicators from MalwareBazaar
- File upload scanning via web UI -- any file type supported (pdf, images, videos, archives, executables)
- Scan history tracking with timestamped entries
- Clean black, white, and grey interface -- no external CSS frameworks
- Cross-platform (Windows, macOS, Linux)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| CLI framework | Typer |
| Terminal output | Rich |
| HTTP client | httpx |
| Web framework | FastAPI |
| Templates | Jinja2 |
| ORM | SQLAlchemy |
| Database | SQLite (dev), PostgreSQL (production) |
| Seed data | MalwareBazaar public CSV export |
| Server | Uvicorn |

## Project Structure

```
signa/
  cli/              CLI application
    hasher.py       Chunked SHA-256 hashing
    client.py       HTTP client for API lookup
    main.py         Typer entry point with scan and lookup commands
  api/              FastAPI backend
    main.py         Application entry point and route registration
    routes.py       API endpoint definitions
    models.py       Pydantic request/response models
    database.py     SQLAlchemy engine and session factory
  db/               Database layer
    schema.py       SQLAlchemy ORM models (ThreatHash)
    seed.py         MalwareBazaar feed import script
  ui/               Web UI
    routes.py       Page routes (hash lookup, file upload, history)
    templates/      Jinja2 HTML templates
  data/             Local SQLite database storage
  tests/            Unit tests
```

## Installation

### Prerequisites

- Python 3.11 or later
- pip

### Setup

```bash
git clone https://github.com/yourusername/signa.git
cd signa

pip install -r requirements.txt
```

### Seed the Database

This fetches the latest malware hashes from MalwareBazaar and stores them locally.

```bash
python -m db.seed
```

To fetch a specific number of records:

```bash
python -m db.seed --limit 500
```

## Usage

### Web UI

Start the server:

```bash
python -m api.main
```

Open http://127.0.0.1:8000 in your browser. You can paste a SHA-256 hash for lookup or upload a file to be hashed and checked against the database.

### CLI

Scan a file:

```bash
python -m cli.main scan path/to/file.exe
```

Look up a hash directly:

```bash
python -m cli.main lookup 094fd325049b8a9cf6d3e5ef2a6d4cc6a567d7d49c35f8bb8dd9e3c6acf3d78d
```

Show help:

```bash
python -m cli.main --help
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Web UI home page |
| GET | `/result?hash={sha256}` | Hash lookup result page |
| POST | `/upload` | File upload scanning |
| GET | `/history` | Scan history page |
| GET | `/api/lookup/{sha256}` | JSON API endpoint |

## Database Schema

**threat_hashes** -- Main lookup table storing known malware indicators.

| Column | Type | Description |
|--------|------|-------------|
| sha256 | String(64) PK | SHA-256 hash |
| family | String(100) | Malware family label (Emotet, RedLine, etc.) |
| severity | String(20) | malicious / suspicious / unknown |
| confidence | Float | 0.0 to 1.0 |
| source | String(100) | Data source (MalwareBazaar, etc.) |
| first_seen | DateTime | First sighting timestamp |
| last_seen | DateTime | Most recent sighting timestamp |

**scan_history** -- Optional audit log of all lookups.


## Contributing

Contributions are welcome. Please open an issue first to discuss the change, then submit a pull request.

## License

MIT
