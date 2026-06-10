"""
main.py — Typer CLI entry point for Signa.
"""

import re
import sys

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .hasher import hash_file
from .client import lookup_hash

# Typer app instance
app = typer.Typer(
    name="signa",
    help="Privacy-preserving threat intelligence CLI",
)

# Force UTF-8 for Windows terminal
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

console = Console()


# ── Hash validation ──
SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


def is_valid_sha256(hash_str: str) -> bool:
    """Check if a string is exactly 64 hexadecimal characters."""
    return bool(SHA256_PATTERN.match(hash_str))


# ── Display helper ──
def print_result_table(title: str, result: dict):
    """Print a verdict table to the console."""
    table = Table(title=title)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Status", result.get("status", "unknown"))
    table.add_row("Malware Family", result.get("family", "N/A"))
    table.add_row("Confidence", str(result.get("confidence", "N/A")))
    table.add_row("Source", result.get("source", "N/A"))
    table.add_row("First Seen", result.get("first_seen", "N/A"))
    table.add_row("Last Seen", result.get("last_seen", "N/A"))

    console.print(table)


# ── Commands ──

@app.command()
def scan(
    file_path: str = typer.Argument(
        ...,
        help="Path to the file to scan",
    ),
):
    """
    Scan a file by computing its SHA-256 hash locally and looking it
    up against the Signa threat-intelligence database.
    """
    # --- 1. Hash the file ---
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task(description="Hashing file...", total=None)
        try:
            file_hash = hash_file(file_path)
        except FileNotFoundError:
            console.print("[red]ERROR[/] File not found: {}".format(file_path))
            raise typer.Exit(code=1)
        except PermissionError:
            console.print("[red]ERROR[/] Permission denied: {}".format(file_path))
            raise typer.Exit(code=1)
        except IsADirectoryError as e:
            console.print("[red]ERROR[/] {}".format(e))
            raise typer.Exit(code=1)
        except OSError as e:
            console.print("[red]ERROR[/] Cannot read file: {}".format(e))
            raise typer.Exit(code=1)

    console.print("[green]OK[/] SHA-256: [bold]{}[/]".format(file_hash))

    # --- 2. Lookup via API ---
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task(description="Querying Signa API...", total=None)
        try:
            result = lookup_hash(file_hash)
        except ConnectionError as e:
            console.print("[red]ERROR[/] {}".format(e))
            raise typer.Exit(code=1)
        except TimeoutError as e:
            console.print("[red]ERROR[/] {}".format(e))
            raise typer.Exit(code=1)

    print_result_table("Scan Result", result)


@app.command()
def lookup(
    hash_value: str = typer.Argument(
        ...,
        help="64-character SHA-256 hash to look up",
    ),
):
    """
    Look up an already-computed SHA-256 hash directly (skip hashing).
    """
    # --- Validate hash format BEFORE calling the API ---
    if not is_valid_sha256(hash_value):
        console.print(
            "[red]ERROR[/] Invalid SHA-256 hash. "
            "Must be exactly 64 hexadecimal characters (0-9, a-f).\n"
            "Got {} characters instead.".format(len(hash_value))
        )
        raise typer.Exit(code=1)

    # --- Lookup via API ---
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task(description="Querying Signa API...", total=None)
        try:
            result = lookup_hash(hash_value)
        except ConnectionError as e:
            console.print("[red]ERROR[/] {}".format(e))
            raise typer.Exit(code=1)
        except TimeoutError as e:
            console.print("[red]ERROR[/] {}".format(e))
            raise typer.Exit(code=1)

    print_result_table("Lookup Result", result)


if __name__ == "__main__":
    app()
