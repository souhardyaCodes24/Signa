"""
routes.py — Web UI routes using FastAPI + Jinja2 templates.
"""

import hashlib
import re
from pathlib import Path

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import LookupResponse
from db.schema import ThreatHash

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()

VALID_HASH = re.compile(r"^[a-fA-F0-9]{64}$")


def lookup_in_db(hash_value: str, db: Session) -> LookupResponse:
    stmt = select(ThreatHash).where(ThreatHash.sha256 == hash_value)
    row = db.execute(stmt).scalar_one_or_none()
    if row is None:
        return LookupResponse(sha256=hash_value, status="unknown")
    return LookupResponse(
        sha256=row.sha256,
        status=row.severity or "malicious",
        family=row.family,
        confidence=row.confidence,
        source=row.source,
        first_seen=row.first_seen,
        last_seen=row.last_seen,
    )


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    else:
        return f"{size_bytes / 1024 ** 3:.2f} GB"


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@router.get("/result", response_class=HTMLResponse)
def result(request: Request, hash: str = "", db: Session = Depends(get_db)):
    if not hash or not VALID_HASH.match(hash):
        return templates.TemplateResponse(
            request, "index.html",
            {"error": "Invalid hash. Must be exactly 64 hexadecimal characters (0-9, a-f)."},
        )
    data = lookup_in_db(hash, db)
    return templates.TemplateResponse(
        request, "index.html",
        {"result": data.model_dump(), "looked_up_hash": hash},
    )


@router.post("/upload", response_class=HTMLResponse)
async def upload(request: Request, file: UploadFile, db: Session = Depends(get_db)):
    sha = hashlib.sha256()
    total_bytes = 0
    while True:
        chunk = await file.read(8192)
        if not chunk:
            break
        sha.update(chunk)
        total_bytes += len(chunk)

    file_hash = sha.hexdigest()
    file_name = file.filename or "unknown"
    mime_type = file.content_type or "application/octet-stream"

    data = lookup_in_db(file_hash, db)

    return templates.TemplateResponse(
        request, "index.html",
        {
            "result": data.model_dump(),
            "file_name": file_name,
            "file_hash": file_hash,
            "file_size": format_size(total_bytes),
            "file_size_bytes": total_bytes,
            "mime_type": mime_type,
        },
    )


@router.get("/history", response_class=HTMLResponse)
def history(request: Request):
    return templates.TemplateResponse(request, "history.html")
