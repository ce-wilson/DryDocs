"""``web`` — public http(s) acquisition over stdlib urllib.

Two properties are NON-NEGOTIABLE rather than preferences, and both come from
the Q6 connector-shape ruling:

* **The transport is injectable.** ``WebConnector(transport=...)`` is what
  makes the Track-1 tests REAL rather than network-dependent — a test that
  needs the internet to prove the refusal works is a test that gets skipped in
  CI and then does not protect anything.
* **The scheme allow-list is enforced.** A documentation fetcher that will
  follow ``file://`` is an SSRF primitive, and a doc capture has no business
  reading anything but public http(s).

The page-count refusal rides here too: Q6's acceptance says in as many words
that this connector does not ship without it, because an unguarded bulk
scraper is not an acceptable intermediate state. The ceiling is checked
BEFORE the first request, against the fully resolved location list.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Callable

from drydocs_core.run_log import batch_run_log

from ..policy import CapturePolicy
from .base import FetchSource, RawPage, SourceUnavailableError

#: A transport is anything that turns (url, headers, timeout) into
#: (body, content_type). Narrow on purpose — a connector that could pass
#: arbitrary request options would be a connector whose tests do not
#: constrain what it actually sends.
Transport = Callable[[str, dict[str, str], int], tuple[bytes, str | None]]


def urllib_transport(url: str, headers: dict[str, str], timeout: int) -> tuple[bytes, str | None]:
    """The real one. Only ever reached when no transport was injected."""
    req = urllib.request.Request(url, headers=headers)  # - scheme checked by policy
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type")


class WebConnector:
    """Fetches public documentation pages. Acquisition only."""

    name = "web"

    def __init__(
        self,
        *,
        policy: CapturePolicy | None = None,
        transport: Transport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.policy = policy or CapturePolicy.load()
        self._transport = transport or urllib_transport
        self._sleep = sleep

    def _fetch(self, source: FetchSource) -> list[RawPage]:
        # 1. Refuse before touching the network. The location list is already
        #    resolved (from the publisher's manifest), so this is exact.
        self.policy.enforce_ceiling(len(source.locations), max_pages=source.max_pages)

        # 2. Refuse every disallowed scheme up front rather than partway
        #    through — a run that fetched 300 pages and then hit a file:// URL
        #    has already done the thing the allow-list exists to prevent.
        for location in source.locations:
            self.policy.check_scheme(location)

        headers = {"User-Agent": self.policy.user_agent}
        pages: list[RawPage] = []
        for i, location in enumerate(source.locations):
            if i:  # politeness delay BETWEEN requests, never before the first
                self._sleep(self.policy.delay_seconds)
            pages.append(self._fetch_one(location, headers))
        return pages

    def fetch(self, source: FetchSource) -> list[RawPage]:
        """One acquisition batch, wrapped in a run log (G107).

        Delegates to :meth:`_fetch` unchanged — this records that the batch ran
        and what it acquired; it does not change what is fetched. Keeps the
        public name so the ``Connector`` protocol is still satisfied.
        """
        with batch_run_log(
            "docmeta.web",
            source=source.id,
            meta={"connector": "WebConnector"},
        ) as summary:
            pages = self._fetch(source)
            summary["pages fetched"] = len(pages)
            summary["bytes fetched"] = sum(len(page.body) for page in pages)
            return pages

    def _fetch_one(self, location: str, headers: dict[str, str]) -> RawPage:
        last: Exception | None = None
        for attempt in range(self.policy.retries):
            try:
                body, content_type = self._transport(location, headers, self.policy.timeout_seconds)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last = exc
                if attempt < self.policy.retries - 1:
                    self._sleep(self.policy.delay_seconds * (attempt + 1))
                continue
            return RawPage(location=location, body=body, content_type=content_type)
        raise SourceUnavailableError(f"failed to fetch {location}: {last}")
