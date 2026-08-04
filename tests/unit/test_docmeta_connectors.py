"""Track-1 guards for the docmeta connectors (backlog Q6 / Q12).

PORTABLE BY CONSTRUCTION: no network, no credentials, no data root. The web
connector's transport is injected, which is the only reason a test can assert
what it would have sent — a network-dependent test gets skipped in CI and then
protects nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_docmeta.connectors import (
    FiledropConnector,
    RawPage,
    SourceUnavailableError,
    WebConnector,
)
from drydocs_docmeta.connectors.base import Connector, FetchSource
from drydocs_docmeta.policy import (
    CapturePolicy,
    DisallowedSchemeError,
    TooManyPagesError,
)

POLICY = CapturePolicy(
    max_pages=3,
    delay_seconds=0.0,
    timeout_seconds=5,
    retries=2,
    user_agent="test-agent/1.0",
    allowed_schemes=("https", "http"),
)


class _RecordingTransport:
    """Stands in for the network and remembers every call."""

    def __init__(self, body: bytes = b"<html><body><p>hi</p></body></html>") -> None:
        self.calls: list[tuple[str, dict[str, str], int]] = []
        self.body = body

    def __call__(self, url, headers, timeout):  # - Transport signature
        self.calls.append((url, dict(headers), timeout))
        return self.body, "text/html; charset=utf-8"


def _source(*locations: str, max_pages: int | None = None) -> FetchSource:
    return FetchSource(id="s", locations=locations, max_pages=max_pages)


# --------------------------------------------------------------------------- #
# the protocol
# --------------------------------------------------------------------------- #
def test_both_shipped_connectors_satisfy_the_protocol():
    assert isinstance(WebConnector(policy=POLICY, transport=_RecordingTransport()), Connector)
    assert isinstance(FiledropConnector(policy=POLICY), Connector)


def test_a_raw_page_is_bytes_not_text():
    """Decoding is a CLEANING decision. The charset a page declares and the
    charset it is often differ, and guessing at acquisition time destroys the
    evidence needed to tell."""
    page = RawPage(location="x", body=b"\xff\xfe raw")
    assert isinstance(page.body, bytes)
    assert len(page) == len(page.body)


# --------------------------------------------------------------------------- #
# web — the two non-negotiables
# --------------------------------------------------------------------------- #
def test_web_refuses_above_the_ceiling_without_fetching_anything():
    """Q6's acceptance says this connector does not ship without the refusal.
    The assertion that matters is not the exception — it is that the transport
    was never called."""
    transport = _RecordingTransport()
    connector = WebConnector(policy=POLICY, transport=transport)

    with pytest.raises(TooManyPagesError, match="resolves to 4 pages"):
        connector.fetch(_source(*[f"https://x.invalid/{i}" for i in range(4)]))

    assert transport.calls == [], "a refused capture must fetch nothing at all"


def test_web_allows_at_the_ceiling():
    transport = _RecordingTransport()
    pages = WebConnector(policy=POLICY, transport=transport).fetch(
        _source("https://x.invalid/a", "https://x.invalid/b", "https://x.invalid/c")
    )
    assert len(pages) == 3
    assert len(transport.calls) == 3


def test_explicit_opt_in_raises_the_ceiling_for_one_run():
    transport = _RecordingTransport()
    pages = WebConnector(policy=POLICY, transport=transport).fetch(
        _source(*[f"https://x.invalid/{i}" for i in range(5)], max_pages=10)
    )
    assert len(pages) == 5


def test_web_refuses_a_disallowed_scheme_before_any_request():
    """The SSRF guardrail. file:// in a documentation fetcher is either a
    mistake or an attempt to make it read something local."""
    transport = _RecordingTransport()
    connector = WebConnector(policy=POLICY, transport=transport)

    with pytest.raises(DisallowedSchemeError, match="file"):
        connector.fetch(_source("https://x.invalid/ok", "file:///etc/passwd"))

    assert transport.calls == [], "the good URL must not be fetched either"


@pytest.mark.parametrize(
    "bad", ["file:///etc/passwd", "ftp://x.invalid/a", "data:text/html,<b>x", "gopher://x/1"]
)
def test_the_allow_list_is_an_allow_list_not_a_deny_list(bad: str):
    with pytest.raises(DisallowedSchemeError):
        WebConnector(policy=POLICY, transport=_RecordingTransport()).fetch(_source(bad))


def test_web_identifies_itself_rather_than_impersonating_a_browser():
    transport = _RecordingTransport()
    WebConnector(policy=POLICY, transport=transport).fetch(_source("https://x.invalid/a"))
    assert transport.calls[0][1]["User-Agent"] == "test-agent/1.0"


def test_web_delays_between_requests_but_not_before_the_first():
    slept: list[float] = []
    policy = CapturePolicy(
        max_pages=10,
        delay_seconds=0.25,
        timeout_seconds=5,
        retries=1,
        user_agent="t",
        allowed_schemes=("https",),
    )
    WebConnector(policy=policy, transport=_RecordingTransport(), sleep=slept.append).fetch(
        _source("https://x.invalid/a", "https://x.invalid/b", "https://x.invalid/c")
    )
    assert slept == [0.25, 0.25], "N pages means N-1 waits, not N"


def test_web_retries_then_reports_the_source_unavailable():
    attempts: list[str] = []

    def failing(url, headers, timeout):
        attempts.append(url)
        raise TimeoutError("nope")

    with pytest.raises(SourceUnavailableError, match="failed to fetch"):
        WebConnector(policy=POLICY, transport=failing, sleep=lambda _: None).fetch(
            _source("https://x.invalid/a")
        )
    assert len(attempts) == POLICY.retries


def test_a_refusal_and_a_failure_are_different_exceptions():
    """A refusal means we declined on purpose and fetched nothing; an
    unavailable source means we tried and the world said no. Only the second
    is worth retrying, so they must not share a type."""
    assert not issubclass(TooManyPagesError, SourceUnavailableError)
    assert not issubclass(SourceUnavailableError, TooManyPagesError)


# --------------------------------------------------------------------------- #
# filedrop
# --------------------------------------------------------------------------- #
def test_filedrop_reads_a_single_file(tmp_path: Path):
    f = tmp_path / "note.md"
    f.write_text("# hello", encoding="utf-8")
    pages = FiledropConnector(policy=POLICY).fetch(_source(str(f)))
    assert [p.body for p in pages] == [b"# hello"]
    assert pages[0].content_type == "text/markdown"


def test_filedrop_reads_a_directory_in_sorted_order(tmp_path: Path):
    """Sorted so two runs over the same tree produce the same page order and
    therefore the same manifest — otherwise every re-capture 'changes'."""
    for name in ("c.md", "a.md", "b.txt"):
        (tmp_path / name).write_text(name, encoding="utf-8")
    pages = FiledropConnector(policy=POLICY).fetch(_source(str(tmp_path)))
    assert [Path(p.location).name for p in pages] == ["a.md", "b.txt", "c.md"]


def test_filedrop_ignores_unadmitted_suffixes_inside_a_directory(tmp_path: Path):
    (tmp_path / "keep.md").write_text("x", encoding="utf-8")
    (tmp_path / "skip.pdf").write_bytes(b"%PDF-1.4")
    pages = FiledropConnector(policy=POLICY).fetch(_source(str(tmp_path)))
    assert [Path(p.location).name for p in pages] == ["keep.md"]


def test_filedrop_refuses_an_unadmitted_file_named_explicitly(tmp_path: Path):
    """Silently skipping a file the operator NAMED would be the worst
    outcome — they would believe it was ingested."""
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    with pytest.raises(SourceUnavailableError, match="does not admit"):
        FiledropConnector(policy=POLICY).fetch(_source(str(pdf)))


def test_filedrop_reports_a_missing_path(tmp_path: Path):
    with pytest.raises(SourceUnavailableError, match="no such file"):
        FiledropConnector(policy=POLICY).fetch(_source(str(tmp_path / "gone.md")))


def test_filedrop_is_ceilinged_too(tmp_path: Path):
    for i in range(4):
        (tmp_path / f"{i}.md").write_text("x", encoding="utf-8")
    with pytest.raises(TooManyPagesError):
        FiledropConnector(policy=POLICY).fetch(_source(str(tmp_path)))
