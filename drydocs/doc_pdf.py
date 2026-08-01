"""doc_pdf.py — deterministic-ish PDF for design docs via headless Chromium (Epic L / L4).

Renders a design doc's single ``.html`` (the L3 output; its ``@media print`` sheet drives
the layout — L13) to ``.pdf`` with a headless
Chromium-family browser (Brave / Chrome / Edge) using FIXED flags, then normalizes the
PDF's embedded dates so re-runs are STRUCTURALLY identical — same layout, pages, and
anchor positions. It is NOT byte-identical (the PDF trailer ``/ID`` still varies run to
run); that is intentional and acceptable per the L4 acceptance.

Brave renders our docs correctly for VIEWING (IDEAS 2026-07-08 Chrome-vs-Brave note), but
its background services hang headless --print-to-pdf on this box, so the PDF is produced by
Edge/Chrome (identical Chromium print engine + @page CSS). The blank PDF is a
BUILD-ON-DEMAND artifact (PUBLISH-BOUNDARY); the durable artifact is the SCANNED, annotated
PDF from the L6 paper loop.

The pure helpers (``find_browser``, ``normalize_pdf_bytes``, ``print_flags``) are unit-
tested; ``html_to_pdf`` shells out. Stdlib only. classification: Internal-Public (tool).
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

# Ordered by headless-print RELIABILITY, not viewing preference. Brave renders our docs
# correctly for VIEWING (IDEAS 2026-07-08) but its background services HANG headless
# --print-to-pdf on this box; Edge/Chrome are reliable headless. The Chromium print engine
# + @page CSS are identical across all three, so the PDF layout is the same whichever runs.
_BROWSER_CANDIDATES: tuple[str, ...] = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/microsoft-edge",
)

# Chromium writes /CreationDate + /ModDate (D:YYYYMMDDHHmmSS±hh'mm') in the Info dict.
_DATE_RE = re.compile(rb"(/(?:CreationDate|ModDate)\s*\()D:\d{14}[^)]*(\))")
_FIXED_DATE = b"D:00000101000000Z"  # sentinel: a render carries no build time (like the board)


def find_browser(candidates: tuple[str, ...] | None = None) -> Path | None:
    """First existing browser from the candidate list (Brave-first), or None."""
    for c in candidates or _BROWSER_CANDIDATES:
        if Path(c).exists():
            return Path(c)
    return None


def normalize_pdf_bytes(data: bytes) -> bytes:
    """Replace embedded CreationDate/ModDate with a fixed sentinel (best-effort; if the
    dates live in a compressed stream the bytes are returned unchanged)."""
    return _DATE_RE.sub(rb"\1" + _FIXED_DATE + rb"\2", data)


def print_flags(html_path: str | Path, pdf_path: str | Path) -> list[str]:
    """The fixed, deterministic headless print flags. Uses old ``--headless`` (proven for
    ``--print-to-pdf``) plus the flags that stop Chromium/Brave hanging on first-run setup
    and background networking; ``--virtual-time-budget`` stops it waiting on timers."""
    return [
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-sync",
        "--disable-component-update",
        "--disable-dev-shm-usage",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={Path(pdf_path).resolve()}",
        Path(html_path).resolve().as_uri(),
    ]


def html_to_pdf(
    html_path: str | Path, pdf_path: str | Path | None = None, browser: str | Path | None = None
) -> Path:
    """Render ``html_path`` (the design doc's .html; @media print rules apply) to a
    normalized PDF; return its path."""
    html_path = Path(html_path)
    if pdf_path is None:
        pdf_path = html_path.with_suffix(".pdf")
    pdf_path = Path(pdf_path)
    exe = Path(browser) if browser else find_browser()
    if not exe:
        raise RuntimeError("no headless Chromium-family browser found (Brave / Chrome / Edge)")
    with tempfile.TemporaryDirectory() as profile:  # isolate from a running browser instance
        cmd = [str(exe), f"--user-data-dir={profile}", *print_flags(html_path, pdf_path)]
        proc = subprocess.run(cmd, capture_output=True, timeout=180)
    if not pdf_path.exists():
        raise RuntimeError(
            f"PDF not produced by {exe.name}: {proc.stderr.decode('utf-8', 'replace')[-500:]}"
        )
    pdf_path.write_bytes(normalize_pdf_bytes(pdf_path.read_bytes()))
    return pdf_path
