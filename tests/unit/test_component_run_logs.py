"""G107 — every component batch leaves a durable run record, on BOTH paths.

Before this, four run cadences produced no record at all: `drydocs_lineage`'s two
graph writes, `drydocs_docmeta`'s connector acquisitions, and
`scripts/external_vendor_scrape.py`, which printed to stdout only — so a scrape
that ran overnight left nothing behind once the terminal closed.

THE FAILURE PATH IS THE HALF THAT MATTERS, which is why every component here is
tested twice. A run log that only exists when nothing went wrong records exactly
the runs nobody needs to look at.

WHAT IS *NOT* COVERED, and it is not an omission: `drydocs_deepdoc`. G107's
acceptance names it as the fourth component, but the component is a scaffold —
its own `__init__` says `NotImplementedError` until MM10, and both
`investigate_failure()` and `write_findings()` raise on their first line. Wrapping
a function that cannot run would produce a log that opens and immediately closes
with a failure summary, forever, and a test asserting that behaviour would be
asserting the scaffold rather than the run log. It rides MM10.
"""

from __future__ import annotations

import pytest

from drydocs_core.run_log import batch_run_log


@pytest.fixture
def logdir(tmp_path, monkeypatch):
    """A hermetic log directory — a test resolving the developer's real one could
    write into it (the same reason `test_data_zones` pins a tmp data root)."""
    d = tmp_path / "logs"
    d.mkdir()
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(d))
    return d


def _one_log(logdir, stem: str):
    """The single run log written for ``stem``, as text. Asserts there is exactly
    one — two would mean a batch opened a log it never closed and opened another."""
    matches = sorted(logdir.glob(f"load.{stem}.*.log"))
    assert len(matches) == 1, f"expected exactly one {stem} log, found {matches}"
    return matches[0].read_text(encoding="utf-8")


def _parses(body: str) -> dict[str, str]:
    """The header/summary contract `run_log.py` defines, read back as a dict.

    Parsed rather than substring-matched: "the file mentions the word summary" is
    not the same as "the summary block is there and has fields in it".
    """
    fields = {}
    for line in body.splitlines():
        if ":" in line and not line.startswith("="):
            key, _, value = line.partition(":")
            if key.strip():
                fields[key.strip()] = value.strip()
    return fields


# ---- the shared contract ----------------------------------------------------


def test_the_helper_records_a_clean_batch(logdir):
    with batch_run_log("probe.ok", target="drydocs") as summary:
        summary["rows"] = 3

    fields = _parses(_one_log(logdir, "probe.ok"))
    assert fields["loader"] == "probe.ok"
    assert fields["target"] == "drydocs"
    assert fields["rows"] == "3"
    assert fields.get("run id")


def test_an_exception_still_closes_the_log_and_is_re_raised(logdir):
    """The half that matters. The batch's exception must reach the caller
    unchanged AND the log must be closed with a failure summary — a crash that
    also loses its own record is the worst of both."""
    with pytest.raises(ValueError, match="boom"):
        with batch_run_log("probe.fail") as summary:
            summary["rows"] = 1
            raise ValueError("boom")

    body = _one_log(logdir, "probe.fail")
    assert "FAILED: boom" in body, "the failure is not recorded in the log"
    assert "-- summary --" in body, "the log was not closed"
    assert _parses(body)["rows"] == "1", "work done before the failure was lost"


def test_an_unwritable_log_dir_never_breaks_the_batch(tmp_path, monkeypatch):
    """A run log is an audit trail, never the reason a batch fails — the rule
    `drydocs/loaders/base.py` has always followed, now shared."""
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "not-a-dir" / "nested"))
    ran = False
    with batch_run_log("probe.nolog") as summary:
        ran = True
        summary["rows"] = 1
    assert ran, "the batch did not run when its log could not be opened"


# ---- per component ----------------------------------------------------------


def test_lineage_curated_write_records_its_batch(logdir, monkeypatch):
    from drydocs_lineage import writer

    monkeypatch.setattr(writer, "_write_curated", lambda *a, **k: 7)
    written = writer.write_curated(object(), {("a", "REL", "b")}, client=object())

    assert written == 7, "the wrapper changed the batch's return value"
    fields = _parses(_one_log(logdir, "lineage.curated"))
    assert fields["rels written"] == "7"
    assert fields["confirmed rels"] == "1"


def test_lineage_curated_failure_is_recorded_and_re_raised(logdir, monkeypatch):
    from drydocs_lineage import writer

    def boom(*a, **k):
        raise RuntimeError("trust boundary")

    monkeypatch.setattr(writer, "_write_curated", boom)
    with pytest.raises(RuntimeError, match="trust boundary"):
        writer.write_curated(object(), {("a", "REL", "b")}, client=object())

    assert "FAILED: trust boundary" in _one_log(logdir, "lineage.curated")


def test_lineage_curated_writes_no_log_when_nothing_was_confirmed(logdir, monkeypatch):
    """The empty guard runs BEFORE the log opens, deliberately: nothing was asked
    for, so there is no batch to record, and a log per no-op call would bury the
    real runs among empties."""
    from drydocs_lineage import writer

    assert writer.write_curated(object(), set()) == 0
    assert not list(logdir.glob("*.log"))


def test_lineage_rua_write_records_its_batch(logdir, monkeypatch):
    from drydocs_lineage import writer

    monkeypatch.setattr(writer, "_write_rua", lambda *a, **k: "report-object")
    assert writer.write_rua(object(), client=object()) == "report-object"
    assert _parses(_one_log(logdir, "lineage.rua"))["report"] == "report-object"


def test_docmeta_connector_records_what_it_acquired(logdir, monkeypatch):
    from drydocs_docmeta.connectors.base import RawPage
    from drydocs_docmeta.connectors.filedrop import FiledropConnector

    pages = [
        RawPage(location="a", body=b"12345", content_type="text/html"),
        RawPage(location="b", body=b"678", content_type="text/html"),
    ]
    monkeypatch.setattr(FiledropConnector, "_fetch", lambda self, source: pages)

    got = FiledropConnector().fetch(_source("bmc-controlm"))

    assert got is pages, "the wrapper changed what the connector returned"
    fields = _parses(_one_log(logdir, "docmeta.filedrop"))
    assert fields["pages fetched"] == "2"
    assert fields["bytes fetched"] == "8"
    assert fields["source"] == "bmc-controlm"


def test_docmeta_connector_failure_is_recorded_and_re_raised(logdir, monkeypatch):
    from drydocs_docmeta.connectors.base import SourceUnavailableError
    from drydocs_docmeta.connectors.filedrop import FiledropConnector

    def boom(self, source):
        raise SourceUnavailableError("drop dir empty")

    monkeypatch.setattr(FiledropConnector, "_fetch", boom)
    with pytest.raises(SourceUnavailableError, match="drop dir empty"):
        FiledropConnector().fetch(_source("bmc-controlm"))

    assert "FAILED: drop dir empty" in _one_log(logdir, "docmeta.filedrop")


def test_the_connector_protocol_still_holds_after_wrapping(logdir):
    """`fetch` stayed the public name on purpose — a wrapper that renamed it
    would silently drop both connectors out of the Connector protocol."""
    from drydocs_docmeta.connectors.base import Connector
    from drydocs_docmeta.connectors.filedrop import FiledropConnector
    from drydocs_docmeta.connectors.web import WebConnector

    assert isinstance(FiledropConnector(), Connector)
    assert isinstance(WebConnector(), Connector)


def test_vendor_scrape_records_its_batch(logdir, monkeypatch):
    """The scrape printed to stdout only, so an overnight run left nothing behind
    once the terminal closed. Its manifest counts now land in a file."""
    import scripts.external_vendor_scrape as scrape

    manifest = {
        "toc_nodes_requested": 12,
        "toc_nodes_recorded": 11,
        "documents": 9,
        "documents_fetched_this_run": 4,
        "documents_skipped_existing": 5,
        "failed": 1,
        "failures": [{"url": "x"}],
        "pages": [],
    }
    monkeypatch.setattr(scrape, "_capture", lambda *a, **k: manifest)
    got = scrape.capture(_FakeTree("bmc-controlm"), [], delay=0.0)

    assert got is manifest, "the wrapper changed the manifest"
    fields = _parses(_one_log(logdir, "scrape.bmc-controlm"))
    assert fields["documents_fetched_this_run"] == "4"
    assert fields["failed"] == "1"
    assert "failures" not in fields, (
        "the summary must carry the COUNTS, not the payload -- a run log is not "
        "a second copy of the manifest"
    )


def test_vendor_scrape_failure_is_recorded_and_re_raised(logdir, monkeypatch):
    import scripts.external_vendor_scrape as scrape

    def boom(*a, **k):
        raise TimeoutError("vendor host unreachable")

    monkeypatch.setattr(scrape, "_capture", boom)
    with pytest.raises(TimeoutError, match="unreachable"):
        scrape.capture(_FakeTree("bmc-controlm"), [], delay=0.0)

    assert "FAILED: vendor host unreachable" in _one_log(logdir, "scrape.bmc-controlm")


class _FakeTree:
    """The one field the wrapper reads."""

    def __init__(self, tree_id: str) -> None:
        self.id = tree_id


def _source(source_id: str):
    """The REAL FetchSource, deliberately — not a stand-in.

    The first cut of these tests used a fake carrying ``source_id``, which is a
    field FetchSource does not have. Both connectors were written against the
    invented name, my tests passed against the same invention, and seventeen
    EXISTING docmeta tests were what caught it. A fake that is allowed to differ
    from the type it stands in for validates the author's belief instead of the
    code.
    """
    from drydocs_docmeta.connectors.base import FetchSource

    return FetchSource(id=source_id, locations=())
