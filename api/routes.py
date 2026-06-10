"""
routes.py — FastAPI route definitions.

One endpoint:
  GET /api/lookup/{sha256}
    → returns a JSON verdict from the threat database
"""

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import LookupResponse
from db.schema import ThreatHash

router = APIRouter(prefix="/api")

# Regex: exactly 64 hex characters
VALID_HASH = re.compile(r"^[a-fA-F0-9]{64}$")


@router.get("/lookup/{sha256}", response_model=LookupResponse)
def lookup_hash(sha256: str, db: Session = Depends(get_db)):
    """
    Look up a 64-character SHA-256 hash in the threat database.
    """
    # Validate hash format before hitting the DB
    if not VALID_HASH.match(sha256):
        raise HTTPException(
            status_code=400,
            detail="SHA-256 must be exactly 64 hexadecimal characters",
        )

    # Query the threat_hashes table
    stmt = select(ThreatHash).where(ThreatHash.sha256 == sha256)
    row = db.execute(stmt).scalar_one_or_none()

    if row is None:
        return LookupResponse(sha256=sha256, status="unknown")

    return LookupResponse(
        sha256=row.sha256,
        status=row.severity or "malicious",
        family=row.family,
        confidence=row.confidence,
        source=row.source,
        first_seen=row.first_seen,
        last_seen=row.last_seen,
    )
