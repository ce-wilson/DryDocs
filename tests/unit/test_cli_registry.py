"""S16 — the composition root DISCOVERS an optional consumer command module, both ways.

The producer ships no ``drydocs/cli_consumer.py``; a consumer (the company port, a Team
Edition instance) may add one on the S8 module shape. This proves both directions with a
FIXTURE module rather than a real one, because the real one must never exist producer-side:

* PRESENT — the fixture is placed on ``drydocs.__path__`` in a fresh interpreter, the root
  is imported, and the fixture's verb is registered LAST (a consumer verb shadows nothing).
* ABSENT — the root imports with nothing on stderr mentioning the module: a missing
  consumer module is the normal producer state and is silent, never a warning.
* ORDER — importing the fixture module first does not execute the root
  (``drydocs.cli`` never lands in ``sys.modules``), the same property
  ``test_cli_import_order.py`` asserts for the six S8 modules, for the same reason.

Every probe is a subprocess: an in-process import proves nothing about import order —
the gap that hid the S13 cycle for two days (J26).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

FIXTURE_MODULE = '''"""A consumer command module, on the S8 shape - fixture only."""
import typer

from drydocs.cli_shared import register_loaders
from drydocs.loaders.base import BaseLoader


class ConsumerProbeLoader(BaseLoader):
    """A loader the producer does not ship."""

    source_id = "controlm-xml-export"

    def load(self, *a, **k):  # pragma: no cover - never run
        raise NotImplementedError


register_loaders(
    {"consumer_probe": ConsumerProbeLoader},
    chains={"consumer-probe": (ConsumerProbeLoader,)},
)

app = typer.Typer()


@app.command(name="consumer-probe")
def consumer_probe() -> None:
    """A verb the producer does not ship."""
    print("probe")
'''


def _probe(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
    )


@pytest.fixture
def consumer_dir(tmp_path: Path) -> Path:
    (tmp_path / "cli_consumer.py").write_text(FIXTURE_MODULE, encoding="utf-8", newline="\n")
    return tmp_path


def test_the_producer_ships_no_consumer_module() -> None:
    assert not (REPO_ROOT / "drydocs" / "cli_consumer.py").exists(), (
        "drydocs/cli_consumer.py is the CONSUMER's file (canonical-company); the producer "
        "never ships one - the discovery seam is the point (S16)"
    )


def test_absent_module_is_silent() -> None:
    result = _probe(
        "import drydocs.cli as c; "
        "print(len(c.app.registered_commands)); "
        "assert all(x.name != 'consumer-probe' for x in c.app.registered_commands)"
    )
    assert result.returncode == 0, result.stderr
    assert "cli_consumer" not in result.stderr, (
        "a missing consumer module must be silent - it is the normal producer state:\n"
        + result.stderr
    )


def test_present_module_registers_its_verbs_last(consumer_dir: Path) -> None:
    code = (
        "import drydocs; "
        f"drydocs.__path__.append({str(consumer_dir)!r}); "
        "import drydocs.cli as c; "
        "names=[x.name for x in c.app.registered_commands]; "
        "print(names[-1]); "
        "assert 'consumer-probe' in names"
    )
    result = _probe(code)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith("consumer-probe"), (
        "the consumer's verbs register AFTER every producer module so they can shadow "
        f"nothing by accident; last registered was {result.stdout.strip()!r}"
    )


def test_importing_the_consumer_module_first_does_not_execute_the_root(
    consumer_dir: Path,
) -> None:
    code = (
        "import sys, drydocs; "
        f"drydocs.__path__.append({str(consumer_dir)!r}); "
        "import drydocs.cli_consumer; "
        "assert 'drydocs.cli' not in sys.modules, 'consumer module dragged in the root'"
    )
    result = _probe(code)
    assert result.returncode == 0, result.stderr


def test_present_module_registers_its_loaders_and_the_views_follow(consumer_dir: Path) -> None:
    """The DECLARATION half: a consumer loader registered at import is in the composed
    root's LOADER_REGISTRY, LOADER_SOURCE is re-derived (the D3 gate reads it), and
    the chain it declares is visible - the seventeen-loaders case, in miniature."""
    code = (
        "import drydocs; "
        f"drydocs.__path__.append({str(consumer_dir)!r}); "
        "import drydocs.cli as c; "
        "assert 'consumer_probe' in c.LOADER_REGISTRY; "
        "assert c.LOADER_SOURCE['consumer_probe'] == 'controlm-xml-export'; "
        "assert 'consumer-probe' in c.COMMAND_LOADERS; "
        "assert 'consumer_probe' not in c.unchained_loaders(); "
        "print('ok')"
    )
    result = _probe(code)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_a_consumer_cannot_shadow_a_producer_loader() -> None:
    from drydocs.cli_shared import LOADER_REGISTRY, register_loaders

    name, cls = next(iter(LOADER_REGISTRY.items()))

    class Other(cls):  # type: ignore[misc,valid-type]
        pass

    with pytest.raises(ValueError, match="never shadows"):
        register_loaders({name: Other})
    assert LOADER_REGISTRY[name] is cls, "a refused registration must change nothing"


def test_the_root_names_the_seam_once() -> None:
    """The module name is settled in one constant the relay and MODULE_MAP cite."""
    import drydocs.cli as c

    assert c.CONSUMER_COMMAND_MODULE == "drydocs.cli_consumer"
