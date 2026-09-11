"""render_remediation_lookup.py — the citation chain beside the /remediation fix diff (G85).

Emits ``web/src/generated/remediation-lookup.json``: for every approved change in the
fix-diff frame, the answers to "does the vendor actually say that?" and "why is this
the rule?", walked down the ratified chain in ``config/precedence.yaml`` — vendor
baseline, internal standards, then who owns the thing.

Deterministic first: every citation is a line this renderer FOUND in the corpus file
it names, under the heading it must sit under, carrying the trust tier that file's
provenance allows. A citation it cannot resolve raises; it never degrades into a
softer answer. Read-only: no graph, no network. Drift guard:
``tests/unit/test_remediation_lookup_json.py``.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))

import render_remediation_diff  # noqa: E402

from drydocs_remediation.changes import ApprovedChange  # noqa: E402
from drydocs_remediation.xml_io import Locator, load_document, locate  # noqa: E402

OUT = REPO / "web" / "src" / "generated" / "remediation-lookup.json"
PRECEDENCE = REPO / "config" / "precedence.yaml"
REQUIREMENTS = REPO / "drydocs_remediation" / "module-requirements.md"

#: The marker a search-snippet capture carries. A file holding it may be cited only as a lead.
SNIPPETS_MARKER = "search-result snippets only"

#: The three tiers, each bound to the authority that governs it in config/precedence.yaml.
#: The ORDER comes from that file's authority numbers, never from this dict.
TIERS: dict[str, tuple[str, str, str]] = {
    "vendor": ("bmc-baseline", "What BMC says the object is", "Does the vendor actually say that?"),
    "standards": ("internal-standards", "Platform standards applied", "Why is this the rule?"),
    "team": ("lob-product-team", "Who owns the thing being changed", "Who has to agree to it?"),
}

#: module-requirements.md section 3 is the contract: each trust state and what it may be
#: cited as. The phrase on the right must appear there, so the two cannot drift apart.
VENDOR_TRUST: dict[str, tuple[str, str]] = {
    "VERBATIM": (
        "citable as vendor ground truth",
        "citable as vendor ground truth, as of its capture date",
    ),
    "GROUNDED": (
        "citable as vendor ground truth",
        "citable as vendor ground truth, as of its capture date",
    ),
    "GROUNDED-snippets-only": (
        "citable ONLY as a lead",
        "citable ONLY as a lead: never presented as vendor ground truth",
    ),
}
GAP_PHRASE = "the gap itself is the answer"

VARIABLES_DOC = "external/orchestration/bmc-controlm/controlm-variables.md"
XML_DOC = "external/orchestration/bmc-controlm/controlm-xml-definition-format.md"
GUIDELINES = "knowledge/standards/technology/controlm-guidelines-and-standards.md"
GREENFIELD = "knowledge/standards/technology/controlm-greenfield-job-standard.md"
DEFFOLDER_URL = (
    "https://documents.bmc.com/supportu/9.0.21.000/en-US/Documentation/Utilities/deffolder.htm"
)
DEFJOB_URL = (
    "https://documents.bmc.com/supportu/9.0.21.000/en-US/Documentation/Utilities/defjob.htm"
)


@dataclass(frozen=True)
class Cite:
    doc: str
    anchor: str
    trust: str | None = None  # vendor only; a standard derives its trust from front matter
    h2: str | None = None  # the '## ' heading the cited line must sit under
    source_url: str | None = None


@dataclass(frozen=True)
class GapSpec:
    what: str
    reason: str
    doc: str  # the file that says the gap is still open
    anchor: str
    while_line_says: str  # the gap exists only while the anchored line still says this


#: Which corpus lines answer each change kind. A change kind in the diff with no entry
#: here raises: a change nobody can explain is not one this panel may stay silent about.
CITATIONS: dict[str, dict[str, tuple[Cite, ...]]] = {
    "rename-variable": {
        "vendor": (
            Cite(VARIABLES_DOC, "**Length:** Name **1", "GROUNDED", h2="Authoritative"),
            Cite(
                VARIABLES_DOC,
                "Name cannot start with a numeric digit",
                "GROUNDED",
                h2="Authoritative",
            ),
            Cite(
                VARIABLES_DOC,
                "must be **Global** to resolve a variable used in a job's",
                "GROUNDED",
                h2="Authoritative",
            ),
            Cite(
                XML_DOC,
                "The NAME + VALUE form is not documented on any captured page.",
                "GROUNDED",
                h2="Variables in definition XML",
                source_url=DEFJOB_URL,
            ),
            Cite(
                XML_DOC,
                "Our target, 9.0.21.300, is inside the supported-but-deprecated window.",
                "GROUNDED",
                h2="Deprecation",
                source_url=DEFFOLDER_URL,
            ),
        ),
        "standards": (
            Cite(GUIDELINES, "Command jobs carry `LAUNCHER_SCRIPT_PATH`", h2="Author's checklist"),
            Cite(
                GUIDELINES, "No forbidden character in any variable name", h2="Author's checklist"
            ),
            Cite(GREENFIELD, "| `LAUNCHER_SCRIPT_PATH` | folder |"),
        ),
    },
}

GAPS: dict[tuple[str, str], tuple[GapSpec, ...]] = {
    ("rename-variable", "vendor"): (
        GapSpec(
            what="the schema that decides the VARIABLE form (.dtd / .xsd)",
            reason=(
                "no captured BMC page documents the NAME + VALUE form this diff edits, and the "
                "schema files that would settle it sit on the Control-M/EM host, not the docs "
                "site; they are not acquired"
            ),
            doc="drydocs_remediation/module-requirements.md",
            anchor="| Utility `.dtd` files",
            while_line_says="NOT ACQUIRED",
        ),
    ),
}


def _lines(rel: str) -> list[str]:
    return (REPO / rel).read_text(encoding="utf-8").splitlines()


def _anchor_line(rel: str, lines: list[str], anchor: str) -> int:
    hits = [n for n, line in enumerate(lines, 1) if anchor in line]
    if len(hits) != 1:
        raise LookupError(
            f"{rel}: anchor {anchor!r} matches {len(hits)} line(s); a citation needs exactly one"
        )
    return hits[0]


def _headings_before(lines: list[str], n: int) -> list[tuple[int, str]]:
    """(level, text) of every heading above line ``n``, skipping fenced code."""
    out: list[tuple[int, str]] = []
    fenced = False
    for line in lines[: n - 1]:
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced and line.startswith("#"):
            out.append((len(line) - len(line.lstrip("#")), line.lstrip("#").strip()))
    return out


def _check_h2(rel: str, heads: list[tuple[int, str]], n: int, h2: str | None) -> None:
    if h2 is None:
        return
    level_two = [text for level, text in heads if level == 2]
    if not level_two or h2 not in level_two[-1]:
        found = level_two[-1] if level_two else "no '## ' heading"
        raise LookupError(f"{rel}:{n} sits under {found!r}, not under a heading naming {h2!r}")


def _excerpt(line: str) -> str:
    text = line.strip()
    if text.startswith("|"):
        text = " · ".join(c.strip() for c in text.strip("|").split("|") if c.strip())
    text = re.sub(r"^(?:[-*]|\d+\.)\s+", "", text)
    text = re.sub(r"^\[[ xX]\]\s+", "", text)
    return text.replace("**", "").replace("`", "").strip()


def _captured(lines: list[str]) -> str | None:
    for line in lines[:40]:
        match = re.search(r"\*\*Date Scraped:\*\*\s*(\d{4}-\d{2}-\d{2})", line)
        if match:
            return match.group(1)
    return None


def _front_matter(rel: str, lines: list[str]) -> dict:
    if not lines or lines[0].strip() != "---":
        raise LookupError(f"{rel}: a standards citation needs the file's YAML front matter")
    end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    return yaml.safe_load("\n".join(lines[1:end]))


def resolve_vendor(spec: Cite) -> dict:
    """One vendor citation, or an error. Refuses SYNTHESIZED and refuses to launder a lead."""
    if spec.trust not in VENDOR_TRUST:
        raise ValueError(
            f"{spec.doc}: trust {spec.trust!r} may not be cited in the vendor tier "
            f"(allowed: {', '.join(VENDOR_TRUST)})"
        )
    lines = _lines(spec.doc)
    text = "\n".join(lines)
    if SNIPPETS_MARKER in text and spec.trust != "GROUNDED-snippets-only":
        raise ValueError(
            f"{spec.doc} is a search-snippet capture; a citation from it must say "
            f"GROUNDED-snippets-only, not {spec.trust}"
        )
    if spec.source_url and spec.source_url not in text:
        raise LookupError(f"{spec.doc}: does not record the source URL {spec.source_url}")
    n = _anchor_line(spec.doc, lines, spec.anchor)
    heads = _headings_before(lines, n)
    _check_h2(spec.doc, heads, n, spec.h2)
    return {
        "doc": spec.doc,
        "line": n,
        "section": heads[-1][1] if heads else "",
        "excerpt": _excerpt(lines[n - 1]),
        "trust": spec.trust,
        "citable_as": VENDOR_TRUST[spec.trust][1],
        "captured": _captured(lines),
        "source_url": spec.source_url,
    }


def resolve_standard(spec: Cite) -> dict:
    """One internal-standards citation; its trust is whatever the file's front matter declares."""
    lines = _lines(spec.doc)
    front = _front_matter(spec.doc, lines)
    if front.get("authority") != "internal-standards":
        raise LookupError(f"{spec.doc}: front matter authority is {front.get('authority')!r}")
    n = _anchor_line(spec.doc, lines, spec.anchor)
    heads = _headings_before(lines, n)
    _check_h2(spec.doc, heads, n, spec.h2)
    return {
        "doc": spec.doc,
        "line": n,
        "section": heads[-1][1] if heads else "",
        "excerpt": _excerpt(lines[n - 1]),
        "trust": front["trust_tier"],
        "citable_as": (
            f"internal standard, status {front['status']}: refines the vendor baseline, "
            "never redefines it"
        ),
        "captured": None,
        "source_url": None,
    }


def _gap(spec: GapSpec) -> dict:
    lines = _lines(spec.doc)
    n = _anchor_line(spec.doc, lines, spec.anchor)
    if spec.while_line_says not in lines[n - 1]:
        raise LookupError(
            f"{spec.doc}:{n} no longer says {spec.while_line_says!r}: the gap "
            f"{spec.what!r} may be closed; cite what closed it and drop the GapSpec"
        )
    return {"what": spec.what, "reason": spec.reason}


def _team_answer(change: ApprovedChange, team_source: str) -> dict:
    """Ownership is never answerable from a published artifact; say why for THIS folder."""
    doc = load_document(render_remediation_diff.DEMO_XML)
    folder = locate(
        doc, Locator(folder=change.locator.folder, data_center=change.locator.data_center)
    )
    seal = any(
        child.tag.upper() == "VARIABLE" and child.attr_value("NAME").lstrip("%") == "SEAL"
        for child in folder.children
    )
    entry = (
        "it declares a SEAL, so the chain has an entry point"
        if seal
        else "it declares no SEAL variable, so the LOB -> Product -> Team chain has no entry point"
    )
    return {
        "tier": "team",
        "status": "gap",
        "citations": [],
        "gaps": [
            {
                "what": f"the team that owns folder {change.locator.folder}",
                "reason": (
                    f"{entry}; and the chain itself lives in {team_source}, which is "
                    "Internal and resolves company-side, never in a published artifact"
                ),
            }
        ],
    }


def _tiers(precedence: dict) -> list[dict]:
    authorities = {a["id"]: a for a in precedence["order"]}
    tiers = []
    for tier_id, (authority_id, title, question) in TIERS.items():
        if authority_id not in authorities:
            raise LookupError(f"config/precedence.yaml has no authority {authority_id!r}")
        if not precedence["active"].get(authority_id):
            raise LookupError(f"config/precedence.yaml marks {authority_id!r} inactive")
        authority = authorities[authority_id]
        tiers.append(
            {
                "id": tier_id,
                "authority_id": authority_id,
                "authority": authority["authority"],
                "title": title,
                "question": question,
                "source": authority["source"],
            }
        )
    return sorted(tiers, key=lambda t: t["authority"])


def build_remediation_lookup() -> dict:
    """The whole frame. Pure: reads committed files, writes nothing."""
    precedence = yaml.safe_load(PRECEDENCE.read_text(encoding="utf-8"))
    requirements = REQUIREMENTS.read_text(encoding="utf-8")
    for phrase, _ in VENDOR_TRUST.values():
        if phrase not in requirements:
            raise LookupError(f"module-requirements.md section 3 no longer says {phrase!r}")
    if GAP_PHRASE not in requirements:
        raise LookupError(f"module-requirements.md section 3 no longer says {GAP_PHRASE!r}")

    tiers = _tiers(precedence)
    team_source = next(t["source"] for t in tiers if t["id"] == "team")
    lookups = []
    for change in render_remediation_diff.DEMO_CHANGES:
        if change.kind not in CITATIONS:
            raise LookupError(
                f"change kind {change.kind!r} ({change.approval_id}) has no citation table"
            )
        table = CITATIONS[change.kind]
        answers = []
        for tier in tiers:
            if tier["id"] == "team":
                answers.append(_team_answer(change, team_source))
                continue
            resolve = resolve_vendor if tier["id"] == "vendor" else resolve_standard
            citations = [resolve(spec) for spec in table.get(tier["id"], ())]
            gaps = [_gap(spec) for spec in GAPS.get((change.kind, tier["id"]), ())]
            answers.append(
                {
                    "tier": tier["id"],
                    "status": "cited" if citations else "gap",
                    "citations": citations,
                    "gaps": gaps,
                }
            )
        subject = f"{change.detail} → {change.value}" if change.value else change.detail
        lookups.append(
            {
                "approval_id": change.approval_id,
                "kind": change.kind,
                "subject": subject,
                "answers": answers,
            }
        )

    return {
        "note": (
            "GENERATED by scripts/render_remediation_lookup.py — never hand-edit; "
            "regenerate with a default-paths render_board.py run"
        ),
        "provenance": (
            "Deterministic citations over the SYNTHESIZED demo diff: every row is a line the "
            "renderer found in the corpus file it names. Nothing here was written by an agent."
        ),
        "agent_seam": (
            "No live agent call is wired. This panel is the precomputed half of the lookup: "
            "a live answer is its own seam in the console's agent tier, never a QuerySpec, "
            "and it would have to cite these same rows."
        ),
        "fix_id": render_remediation_diff.build_remediation_diff()["fix_id"],
        "trust_ladder": [
            {"trust": trust, "citable_as": citable_as}
            for trust, (_, citable_as) in VENDOR_TRUST.items()
        ]
        + [{"trust": "blocked", "citable_as": f"not citable: {GAP_PHRASE}"}],
        "tiers": tiers,
        "lookups": lookups,
    }


def main() -> None:
    data = build_remediation_lookup()
    OUT.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    cited = sum(len(a["citations"]) for lk in data["lookups"] for a in lk["answers"])
    print(f"wrote {OUT} ({len(data['lookups'])} change(s), {cited} citation(s))")


if __name__ == "__main__":
    main()
