"""
seed.py — fetches real malware SHA-256 hashes from MalwareBazaar's
public CSV export (no API key needed) and stores them in your local
SQLite database.

Once seeded, the CLI will return "malicious" instead of "unknown"
for any hash that exists in the database.

Usage:
    python -m db.seed             # fetch ~250 recent malware hashes
    python -m db.seed --limit 50  # fetch fewer
"""

import argparse
import csv
from datetime import datetime
from io import StringIO

import httpx
from sqlalchemy.orm import Session

# Import our DB engine and models
from api.database import engine, SessionLocal
from db.schema import Base, ThreatHash


# ── MalwareBazaar public CSV export (no auth required) ──
CSV_URL = "https://bazaar.abuse.ch/export/csv/recent/"


# ── A few well-known malware hashes for spot-checking ──
# These are publicly documented samples from MalwareBazaar.
# You can look them up directly after seeding.
WELL_KNOWN_SAMPLES = [
    {
        "sha256": "094fd325049b8a9cf6d3e5ef2a6d4cc6a567d7d49c35f8bb8dd9e3c6acf3d78d",
        "family": "Emotet",
        "severity": "malicious",
        "confidence": 1.0,
        "source": "MalwareBazaar (known sample)",
    },
]


def fetch_csv(limit: int = 250) -> list[dict]:
    """
    Download MalwareBazaar's CSV export of recent malware.
    CSV columns (first 5 rows are header comments starting with '#'):
      id, md5_hash, sha1_hash, sha256_hash, first_seen, last_seen,
      signature, file_type, tags, ...
    """
    headers = {
        "User-Agent": "Signa/0.1 (threat-intelligence CLI)",
    }
    with httpx.Client(timeout=60.0, headers=headers, follow_redirects=True) as client:
        resp = client.get(CSV_URL)

    if resp.status_code != 200:
        print(f"ERROR: MalwareBazaar CSV returned HTTP {resp.status_code}")
        return []

    # The CSV has comment lines starting with '#', skip them
    lines = resp.text.splitlines()
    data_lines = [l for l in lines if not l.startswith("#")]

    # The CSV has NO header row. Columns are:
    # first_seen, sha256_hash, md5_hash, sha1_hash, reporter,
    # file_name, file_type_guess, mime_type, signature, clamav,
    # vtpercent, imphash, ssdeep, tls_hash
    fieldnames = [
        "first_seen", "sha256_hash", "md5_hash", "sha1_hash",
        "reporter", "file_name", "file_type_guess", "mime_type",
        "signature", "clamav", "vtpercent", "imphash", "ssdeep", "tls_hash",
    ]

    reader = csv.DictReader(
        StringIO("\n".join(data_lines)),
        fieldnames=fieldnames,
        skipinitialspace=True,  # handle ", " separator style
    )
    records = []
    for i, row in enumerate(reader):
        if i >= limit:
            break
        records.append(row)

    return records


def parse_timestamp(ts_str: str | None) -> datetime | None:
    """
    MalwareBazaar returns timestamps like "2024-01-15 12:30:00".
    Parse them or return None if missing.
    """
    if not ts_str:
        return None
    try:
        return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def upsert_hash(db: Session, record: dict):
    """
    Insert or update a single threat hash row from a CSV record.
    CSV columns: sha256_hash, first_seen, last_seen, signature, ...
    If the hash already exists (same sha256), update the metadata.
    """
    sha256 = (record.get("sha256_hash") or "").strip().strip('"')
    if not sha256 or len(sha256) != 64:
        return  # skip invalid rows

    family = (record.get("signature") or "").strip().strip('"')
    if family.lower() in ("", "n/a", "none"):
        family = None

    first_seen = parse_timestamp(record.get("first_seen", "").strip().strip('"'))
    last_seen  = parse_timestamp(record.get("last_seen", "").strip().strip('"'))

    # Check if this hash already exists
    existing = db.query(ThreatHash).filter(ThreatHash.sha256 == sha256).first()

    if existing:
        if family and not existing.family:
            existing.family = family
        if first_seen and (not existing.first_seen or first_seen < existing.first_seen):
            existing.first_seen = first_seen
        if last_seen and (not existing.last_seen or last_seen > existing.last_seen):
            existing.last_seen = last_seen
        existing.source = "MalwareBazaar"
        existing.severity = "malicious"
    else:
        row = ThreatHash(
            sha256=sha256,
            family=family,
            severity="malicious",
            confidence=1.0,
            source="MalwareBazaar",
            first_seen=first_seen,
            last_seen=last_seen,
        )
        db.add(row)


def main():
    parser = argparse.ArgumentParser(description="Seed Signa DB with malware hashes")
    parser.add_argument("--limit", type=int, default=100, help="Number of hashes to fetch (max 1000)")
    args = parser.parse_args()

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    # ── 1. Insert well-known samples ──
    print("Inserting known reference samples...")
    db = SessionLocal()
    try:
        for sample in WELL_KNOWN_SAMPLES:
            record = {
                "sha256": sample["sha256"],
                "family": sample["family"],
                "severity": sample["severity"],
                "confidence": sample["confidence"],
                "source": sample["source"],
            }
            upsert_hash(db, record)
        db.commit()
        known_count = len(WELL_KNOWN_SAMPLES)
        print(f"  Added {known_count} reference hashes")
    except Exception as e:
        db.rollback()
        print(f"  [red]ERROR[/] inserting reference hashes: {e}")
    finally:
        db.close()

    # ── 2. Fetch from MalwareBazaar CSV ──
    print(f"Fetching up to {args.limit} recent malware hashes from MalwareBazaar...")
    records = fetch_csv(args.limit)
    print(f"  Got {len(records)} records from CSV")

    db = SessionLocal()
    try:
        for record in records:
            upsert_hash(db, record)
        db.commit()
        print(f"  Stored {len(records)} hashes in database")
    except Exception as e:
        db.rollback()
        print(f"  ERROR storing hashes: {e}")
    finally:
        db.close()

    # ── Summary ──
    db = SessionLocal()
    try:
        total = db.query(ThreatHash).count()
        print(f"\n[green]Done![/] Database now has {total} threat indicators.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
