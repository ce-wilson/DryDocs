"""Definition interchange formats — the format-agnostic seam (0002-B §2 step 4).

The target environment imports/exports job & folder *definitions* as XML
(Control-M 9.0.21.300), but XML is being phased out for BMC's JSON Automation API
(name-as-key). Everything above this module speaks :class:`DefinitionSet`; only a
:class:`DefinitionFormat` implementation may know the wire shape.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DefinitionSet:
    """A parsed set of Control-M definitions (folders + jobs), format-independent.

    Deliberately thin at scaffold time — the real shape is settled by the M0 PoC
    against ``drydocs_core.models`` (do NOT grow a parallel model layer here;
    shared shapes belong in core).
    """

    folders: list[Any] = field(default_factory=list)
    jobs: list[Any] = field(default_factory=list)
    source: str | None = None  # provenance of the loaded artifact (path/export id)


class DefinitionFormat(ABC):
    """Load/dump boundary for definition artifacts. XML impl now, JSON impl later."""

    @abstractmethod
    def load(self, source: Path) -> DefinitionSet:
        """Parse a definition artifact into a :class:`DefinitionSet`."""

    @abstractmethod
    def dump(self, definitions: DefinitionSet, target: Path) -> Path:
        """Write a :class:`DefinitionSet` as a definition artifact; returns the path."""


class XmlDefinitionFormat(DefinitionFormat):
    """Control-M definition XML (ctmdeffolder/ctmdefine shapes) — the current wire format."""

    def load(self, source: Path) -> DefinitionSet:  # noqa: ARG002
        raise NotImplementedError("M0 PoC slice — see internal/remediation/controlm-remediation-m0-poc-scope.md")

    def dump(self, definitions: DefinitionSet, target: Path) -> Path:  # noqa: ARG002
        raise NotImplementedError("M0 PoC slice — greenfield export")
