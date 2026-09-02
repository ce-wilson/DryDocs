"""Write an assembled page to a local file for offline preview (no publish)."""

from __future__ import annotations

from pathlib import Path


def write_preview(content: str, out_path: str | Path) -> Path:
    """Write ``content`` to ``out_path`` (creating parent dirs). Returns the path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # J49: LF — an offline preview is compared against the published page; line
    # endings must not be the diff. Caller-chosen path, not a committed surface.
    out_path.write_text(content, encoding="utf-8", newline="\n")
    return out_path
