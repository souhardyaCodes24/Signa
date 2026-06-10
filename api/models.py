"""
models.py — Pydantic models that define the shape of API
requests and responses. FastAPI uses these automatically for
validation and OpenAPI docs.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Response returned by GET /api/lookup/{sha256} ──
class LookupResponse(BaseModel):
    """
    The verdict for a single hash lookup.
    All fields optional because the hash might be unknown.
    """
    sha256: str
    status: str                     # "malicious" | "clean" | "unknown"
    family: Optional[str] = None    # malware family label
    confidence: Optional[float] = None
    source: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


# ── Generic error envelope ──
class ErrorResponse(BaseModel):
    detail: str
