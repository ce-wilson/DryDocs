"""The rename check reads the producer tree through ONE pipe (PORT1 c).

``scripts/port_rename_check.py`` used to spawn one ``git show`` per producer file - a
whole-tree look was ~1,900 processes and 109 s on this tree. ``git cat-file --batch``
reads the same blobs over one pipe in 8 s. What must hold is that the blobs come back
IDENTICAL to what ``git show`` decoded, per path, and that an object that does not
resolve is skipped the way the failed ``git show`` was - never fatal, never a wrong
pairing of the next path with the previous body.
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "port_rename_check.py"


def _script():
    spec = importlib.util.spec_from_file_location("port_rename_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _show(path: str) -> str:
    return subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    ).stdout


def test_the_batch_read_matches_git_show_per_path_and_skips_a_missing_object() -> None:
    module = _script()
    paths = ["PORT-MANIFEST.yaml", "docs/no/such/file.md", "MODULE_MAP.md", "README.md"]
    blobs = module._blobs("HEAD", paths)
    assert set(blobs) == {"PORT-MANIFEST.yaml", "MODULE_MAP.md", "README.md"}
    for path in blobs:
        assert blobs[path] == _show(path), f"{path}: the batch read differs from git show"


def test_the_batch_decode_is_the_git_show_decode() -> None:
    """UTF-8 with replacement, then universal newlines - the two things ``text=True,
    encoding="utf-8", errors="replace"`` did to ``git show``'s bytes."""
    module = _script()
    assert module._decode(b"a\r\nb\rc\n") == "a\nb\nc\n"
    assert module._decode(b"\xe2\x80\x94 \x9d") == "— �"


def test_the_producer_side_no_longer_spawns_a_process_per_file() -> None:
    """The reason the change was made, pinned as code: ``git show`` is not called
    from the producer read at all."""
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    shows = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_git"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "show"
    ]
    assert not shows, "producer_files went back to one `git show` per file"
