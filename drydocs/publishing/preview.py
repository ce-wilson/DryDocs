"""Write an assembled page to a local file for offline preview (no publish)."""
from __future__ import annotations

from pathlib import Path


def write_preview(content: str, out_path: str | Path) -> Path:
    """Write ``content`` to ``out_path`` (creating parent dirs). Returns the path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    return out_path
