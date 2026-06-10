"""
hasher.py — computes SHA-256 hash of a file in fixed-size chunks
so that even multi-GB files never fill up RAM.
"""

import hashlib
from pathlib import Path


CHUNK_SIZE = 8192  # 8 KB per read


def hash_file(file_path: str) -> str:
    """
    Read a file chunk-by-chunk, compute its SHA-256 digest,
    and return the 64-character hex string.
    """
    path = Path(file_path).resolve()

    # Check for common errors before opening
    if not path.exists():
        raise FileNotFoundError(str(path))
    if path.is_dir():
        raise IsADirectoryError("'{}' is a directory, not a file".format(path))

    sha = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha.update(chunk)

    return sha.hexdigest()
