"""Doc-capture policy — the Q12 guardrail's numbers, read from config.

Q12's acceptance requires the page-count threshold and the per-request delay
to be CONFIG values rather than hardcoded literals. They are policy about how
we treat a third party, not a detail of whichever entrypoint happens to run,
so both the standalone vendor scraper and the component's web connector read
this one file — otherwise "too many pages" would mean different things
depending on which door the operator used.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parents[1])
DEFAULT_POLICY_PATH = _REPO_ROOT / "config" / "doc-capture.yaml"
SCHEMA = "drydocs.doc-capture.v1"


class TooManyPagesError(RuntimeError):
    """A capture resolved to more pages than the operator sized it for."""


class DisallowedSchemeError(ValueError):
    """A URL whose scheme is outside the allow-list (the SSRF guardrail)."""


@dataclass(frozen=True)
class CapturePolicy:
    max_pages: int
    delay_seconds: float
    timeout_seconds: int
    retries: int
    user_agent: str
    allowed_schemes: tuple[str, ...]

    @classmethod
    def load(cls, path: str | Path | None = None) -> CapturePolicy:
        raw = yaml.safe_load(Path(path or DEFAULT_POLICY_PATH).read_text(encoding="utf-8"))
        if raw.get("schema") != SCHEMA:
            raise ValueError(f"expected schema {SCHEMA}, got {raw.get('schema')!r}")
        c = raw["capture"]
        return cls(
            max_pages=int(c["max_pages"]),
            delay_seconds=float(c["delay_seconds"]),
            timeout_seconds=int(c["timeout_seconds"]),
            retries=int(c["retries"]),
            user_agent=str(c["user_agent"]),
            allowed_schemes=tuple(c["allowed_schemes"]),
        )

    # ---- the two guardrails ------------------------------------------------

    def enforce_ceiling(self, page_count: int, *, max_pages: int | None = None) -> None:
        """Refuse rather than start a run nobody sized.

        A PRE-FLIGHT refusal, not a mid-run abort: every tree we capture
        publishes a machine-readable table of contents, so the exact page count
        is known before the first content request. Nothing crawls, so nothing
        discovers its own size halfway through.
        """
        ceiling = self.max_pages if max_pages is None else max_pages
        if page_count > ceiling:
            raise TooManyPagesError(
                f"REFUSING: this capture resolves to {page_count} pages, above the "
                f"ceiling of {ceiling}. Nothing was fetched. Raise the ceiling "
                f"explicitly if that is genuinely intended, or narrow the subtree. "
                f"Check the tree listing first: picking the wrong tree is the common "
                f"cause of an unexpectedly large count."
            )

    def check_scheme(self, url: str) -> None:
        """The SSRF allow-list. A doc capture has no business reaching
        ``file://``, ``ftp://`` or a ``data:`` URI."""
        scheme = url.split(":", 1)[0].lower() if ":" in url else ""
        if scheme not in self.allowed_schemes:
            raise DisallowedSchemeError(
                f"scheme {scheme or '(none)'!r} is not in the doc-capture allow-list "
                f"{list(self.allowed_schemes)} — refusing {url!r}"
            )
