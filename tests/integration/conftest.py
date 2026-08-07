"""Integration-suite environment defaults (J36).

**Ryuk is disabled by DEFAULT here, and why (J18 venue: the producer Windows
desktops — Docker Desktop on Windows 11; observed on the primary desktop at the
G23 e2e close, 2026-08-07).** Testcontainers starts a sidecar reaper container
("ryuk") whose host-port mapping intermittently fails on this machine class:

    Port mapping ... port 8080 is not available

The conflict is INTERMITTENT — at the J36 investigation nothing occupied 8080
and no Windows excluded-port range covered it, yet the failure reproduced
identically on an existing J9 test the day before. Two documented Windows
mechanisms produce exactly this shape: (a) Hyper-V/WinNAT excluded TCP port
ranges shift on reboot and can swallow the mapped port
(``netsh interface ipv4 show excludedportrange protocol=tcp``), and (b) a ryuk
container left behind by a crashed earlier run still holds its mapping. An
intermittent startup failure in the shared fixture reads as "the tests are
flaky", which is worse than losing what ryuk buys us:

- Ryuk's ONLY job is reaping containers when the test process dies without
  running teardown. ``Neo4jContainer``'s context manager already stops the
  container on every ordinary pass/fail path.
- CI runners are ephemeral; a leaked container dies with the runner.
- The residual risk — a hard-killed local run leaks one Neo4j container — has
  a one-line cleanup, below.

``setdefault`` keeps this an OVERRIDABLE default, not a mandate: export
``TESTCONTAINERS_RYUK_DISABLED=false`` before pytest to re-enable the reaper
on a machine where it behaves.

**Stale-container cleanup (the next-occurrence runbook):**

    docker ps -a --filter ancestor=testcontainers/ryuk   # crashed reapers
    docker ps -a --filter label=org.testcontainers       # leaked test containers
    docker rm -f <id ...>

See also ``internal/repo-README.md`` ("Integration tests" note).
"""

from __future__ import annotations

import os

os.environ.setdefault("TESTCONTAINERS_RYUK_DISABLED", "true")
