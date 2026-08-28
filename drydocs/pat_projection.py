"""Project the raw PAT team report into the two CSVs the dev-team loaders read (G82).

THE GAP THIS CLOSES. ``DevTeamsLoader`` (``pat:product-catalog``, ``dev_teams.cypher``)
and ``PatProductMappingLoader`` (``pat:people-report``, ``pat_product_mapping.cypher``)
are real, wired, registered, and green — against ``drydocs/data/samples/*__sample.csv``.
The step that turns the RAW team report (the PAT ``TEAM_DETAILS_REPORT`` export,
one row per team, ~20 columns) into the two narrow files those loaders consume was
referenced by the company-side loader docstrings and never built. Consequence, and
the reason this module exists: **the dev-team load has never run against real
data.** A sample fixture makes a loader test green independently of whether any
real file can reach it, so "built and tested" and "never run" were both true at
once. ``locator.mapping: ~`` on ``pat:people-report`` was the fingerprint.

WHAT THIS DOES. One raw CSV in, two CSVs out, named exactly as
the team chain expects (``dev_teams__sample.csv`` and
``pat_product_mapping__sample.csv``) so the existing command runs them unchanged::

    poetry run python scripts/project_pat_team_report.py <raw.csv> --out-dir <dir>
    drydocs refresh-reference --samples-dir <dir>

It is a REPEATABLE step, not a one-off: the report is re-exported weekly (the
chain's own cadence), so the projection must be re-runnable and must report what
it did. Nothing here touches the graph.

HEADER BASIS — read before trusting a column name. Only FOUR raw headers are
SME-pinned (source-registry row ``pat:people-report``, C17 / 2026-08-11 evidence):
``Relationship Type`` (the alignment — Aligned / Flex / Dedicated), ``Team Type
Name`` (the DISCIPLINE decoy beside it — NEVER the alignment), ``Legacy Team ID``
(unmodelled), and the semicolon-delimited SEAL-id column. Every other default
spelling in :data:`DEFAULT_HEADER_MAP` is DryDocs' belief about the export,
transcribed from the C17 gate record (ID + Name pairs for Product / Supporting
Area Product / Sponsoring Area Product / Sponsoring Product; Product Line and
Sponsoring Product Line as names only) and the pat-evidence README. So the map is
a PARAMETER, not a constant: the projection REFUSES to guess — a mapped logical
field whose header is absent from the raw file is a hard error naming the header
it looked for, never a silent empty column (see LOUDNESS below for the one
documented exception) — and the first real run pins the spellings with
``--header-map`` (a YAML ``{logical_field: "Raw Header"}``), after
which the ledger ``config/source-mappings/pat-team-report.yaml`` is corrected to
the physical names and ``census: pending`` is closed. Column NAMES are mechanism
(Internal-Public); the raw report and both projected files are Internal and stay
under ``DRYDOCS_DATA_ROOT`` — never in the tree.

LOUDNESS (K30, 2026-08-28). Absence of ANY mapped header is loud, not only the
three in :data:`REQUIRED_FIELDS`. Before K30 a non-required field whose header
was missing degraded to a silently empty column and only landed in
``ProjectionReport.missing_optional`` — a line the CLI printed on a normal,
exit-0 run, easy to miss. There are now exactly two outcomes for a mapped
field whose header the raw file does not carry: it raises (the default), or it
is named in :data:`ACKNOWLEDGED_ABSENT` with a reason (a permanent, documented
exception — not a quiet "optional" tier). ``jira_board_id`` is the first
occupant: it maps to ``"JIRA Board"``, a header ``TEAM_DETAILS_REPORT`` does
not carry — the field lives in a sibling PAT export this module does not read.
Kept mapped rather than dropped so ``DevTeamRow.jira_board_id`` stays a
documented, named gap instead of one more silently absent column.

WHAT IS DELIBERATELY DROPPED, and why it is written here rather than left to
``extra="ignore"``: ``Team Type Name`` (discipline — a property of the TEAM, not of
its relationship to a product; own home, own gate), ``Sponsoring Product Line`` and
``Product Line`` (NAME-ONLY in this report; keying a :ProductLine by name is what
C17 §a forbids), ``Legacy Team ID`` (opaque predecessor key; ``team_id`` is the
only key), LOB / status / agile framework (not consumed by either row model).
Dropped columns are COUNTED in the report so a new column in a re-export is
visible, not silently ignored.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import yaml

#: The two files THIS SCRIPT PRODUCES, by name. They are two of the THREE steps
#: the team chain runs (cli.CHAINS['refresh-teams'] since the G79 split). The
#: third, pat_team_roles, is a HAND-DROP BY RULING (K27, 2026-08-27), not a
#: missing projection: the raw report is one row per TEAM and carries no person
#: columns, so a per-person (team_id, employee_sid, role_id) file cannot be
#: projected from it — the SME hand-authors it from PAT's team-membership view
#: into the same pat/ drop (see the load runbook's Refresh section). Keep in
#: lock-step with drydocs/cli.py. The ``__sample`` suffix is the chain's naming convention, not
#: a claim that the content is synthetic: ``--samples-dir`` is simply "the
#: directory the chain reads", and the projection writes there.
DEV_TEAMS_FILE = "dev_teams__sample.csv"
PAT_PRODUCT_MAPPING_FILE = "pat_product_mapping__sample.csv"

DEV_TEAMS_COLUMNS = ("team_id", "name", "jira_board_id", "parent_product_id")
PAT_PRODUCT_MAPPING_COLUMNS = (
    "team_id",
    "product_id",
    "area_product_id",
    "seal_ids",
    "team_type",
    "sponsored",
    "sponsored_product_id",
    "sponsored_area_product_id",
)

#: logical field -> raw report header. SEE "HEADER BASIS" above: only the four
#: marked PINNED are SME-confirmed spellings; the rest are transcribed beliefs
#: that the first real run confirms or overrides via --header-map.
DEFAULT_HEADER_MAP: dict[str, str] = {
    "team_id": "Team ID",
    "team_name": "Team Name",
    "jira_board_id": "JIRA Board",
    "product_id": "Product ID",
    "supporting_area_product_id": "Supporting Area Product ID",
    "seal_ids": "SEAL IDs",  # PINNED (pat-evidence README): semicolon-delimited
    "relationship_type": "Relationship Type",  # PINNED (SME 2026-08-11): Aligned|Flex|Dedicated
    "sponsoring_product_id": "Sponsoring Product ID",
    "sponsoring_area_product_id": "Sponsoring Area Product ID",
}

#: Logical fields the two row models REQUIRE (DevTeamRow.team_id;
#: PatProductMappingRow.team_id / product_id / team_type). A missing header
#: for any of these is a hard error — the projection never invents a key.
REQUIRED_FIELDS = ("team_id", "product_id", "relationship_type")

#: Mapped logical fields (see LOUDNESS above) whose header is KNOWN to be
#: permanently absent from THIS report — not a spelling gap --header-map will
#: ever close, but a field this raw file simply does not carry. Listing a
#: field here is what keeps (a)'s loudness rule from firing on every normal
#: run; every entry says WHERE the header actually lives so the gap stays
#: legible instead of quietly re-becoming a silent empty column.
ACKNOWLEDGED_ABSENT: dict[str, str] = {
    "jira_board_id": (
        "maps to 'JIRA Board' (DEFAULT_HEADER_MAP); TEAM_DETAILS_REPORT does not "
        "carry it — the field lives in a sibling PAT export this module does not "
        "read. Kept mapped, not dropped, so DevTeamRow.jira_board_id has a named "
        "home if a future projection joins that export in. K30, 2026-08-28."
    ),
}
assert set(ACKNOWLEDGED_ABSENT) <= set(
    DEFAULT_HEADER_MAP
), "ACKNOWLEDGED_ABSENT names a logical field DEFAULT_HEADER_MAP does not map"

#: Raw headers the projection knows it is dropping, with the reason — so the
#: report can say "dropped by design" apart from "unknown column, look at it".
KNOWN_DROPPED: dict[str, str] = {
    "Team Type Name": "discipline (Technology/Product/Design/...), NOT the alignment — not modelled (C17 docstring)",
    "Legacy Team ID": "opaque predecessor key; team_id is the only team key",
    "Product Line": "name-only in this report; :ProductLine is never keyed by name (C17 §a)",
    "Sponsoring Product Line": "name-only; third sponsoring form OUT OF SCOPE (C17 §c)",
    "Product Name": "display name; the id column is the key",
    "Supporting Area Product Name": "display name; the id column is the key",
    "Sponsoring Area Product Name": "display name; the id column is the key",
    "Sponsoring Product Name": "display name; the id column is the key",
    "LOB": "not consumed by either row model; the LOB tier comes from the catalog hierarchy",
    "Status": "not consumed by either row model",
    "Agile Framework": "not consumed by either row model",
    "JIRA Instance": "not consumed; jira_board_id is the modelled field",
}


class ProjectionError(RuntimeError):
    """A required header is absent. Raised, not reported: a projection that
    guesses a KEY column writes wrong rows into a loader that MERGEs on it."""


@dataclass
class ProjectionReport:
    """What the projection read and wrote — the count the loader summary can be
    reconciled against, and the column census the ledger is corrected from."""

    raw_rows: int = 0
    dev_team_rows: int = 0
    mapping_rows: int = 0
    #: raw rows skipped because team_id or product_id was blank (counted, never silent)
    skipped_no_key: int = 0
    #: raw rows whose Relationship Type was not aligned|flex|dedicated — emitted
    #: anyway so the LOADER rejects them (its validator is the authority), counted here
    unrecognised_team_type: int = 0
    #: raw headers actually seen, in file order — the census input for the ledger
    raw_headers: tuple[str, ...] = ()
    #: mapped logical fields listed in ACKNOWLEDGED_ABSENT whose header this
    #: run's raw file did not carry — expected, reported, never raised. Any
    #: OTHER mapped field with a missing header raises ProjectionError instead
    #: of reaching this report at all (K30 — no quiet third path).
    acknowledged_absent: tuple[str, ...] = ()
    #: raw headers neither mapped nor in KNOWN_DROPPED — look at these
    unknown_headers: tuple[str, ...] = ()
    dropped_by_design: tuple[str, ...] = ()
    header_map: dict[str, str] = field(default_factory=dict)

    def lines(self) -> list[str]:
        out = [
            f"raw rows: {self.raw_rows}",
            f"dev_teams rows written: {self.dev_team_rows}",
            f"pat_product_mapping rows written: {self.mapping_rows}",
            f"skipped (no team_id/product_id): {self.skipped_no_key}",
            f"unrecognised Relationship Type (loader will reject): {self.unrecognised_team_type}",
            f"raw headers ({len(self.raw_headers)}): {', '.join(self.raw_headers)}",
        ]
        if self.acknowledged_absent:
            out.append(
                f"acknowledged-absent headers (expected missing, see ACKNOWLEDGED_ABSENT): "
                f"{', '.join(self.acknowledged_absent)}"
            )
        if self.unknown_headers:
            out.append(
                f"UNKNOWN headers (not mapped, not known-dropped): {', '.join(self.unknown_headers)}"
            )
        if self.dropped_by_design:
            out.append(f"dropped by design: {', '.join(self.dropped_by_design)}")
        return out


def load_header_map(path: str | Path | None) -> dict[str, str]:
    """DEFAULT_HEADER_MAP overlaid with a YAML ``{logical_field: "Raw Header"}``."""
    merged = dict(DEFAULT_HEADER_MAP)
    if path:
        override = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        unknown = set(override) - set(DEFAULT_HEADER_MAP)
        if unknown:
            raise ProjectionError(
                f"header map names logical fields the projection does not have: {sorted(unknown)}"
            )
        merged.update({k: str(v) for k, v in override.items()})
    return merged


_VALID_TEAM_TYPES = ("aligned", "flex", "dedicated")


def _blank(value: str | None) -> bool:
    return value is None or not str(value).strip()


def project_rows(
    raw_rows: list[dict[str, str]],
    raw_headers: list[str],
    header_map: dict[str, str] | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], ProjectionReport]:
    """The projection proper — pure, so a test can drive it without files."""
    hmap = header_map or dict(DEFAULT_HEADER_MAP)
    present = set(raw_headers)
    missing_required = [f for f in REQUIRED_FIELDS if hmap[f] not in present]
    if missing_required:
        raise ProjectionError(
            "raw report lacks the header(s) for required field(s) "
            + ", ".join(f"{f} (looked for {hmap[f]!r})" for f in missing_required)
            + f"; raw headers are {raw_headers}. Pin the spelling with --header-map; the "
            "projection does not guess a key column."
        )
    # (a) K30: every OTHER mapped field's absence is loud too — there is no
    # quiet "optional" tier left. A field is allowed to be absent only when it
    # is explicitly named in ACKNOWLEDGED_ABSENT; anything else missing raises
    # exactly like a required field, naming the header it looked for.
    unacknowledged_missing = [
        f
        for f in hmap
        if f not in REQUIRED_FIELDS and f not in ACKNOWLEDGED_ABSENT and hmap[f] not in present
    ]
    if unacknowledged_missing:
        raise ProjectionError(
            "raw report lacks the header(s) for mapped field(s) "
            + ", ".join(f"{f} (looked for {hmap[f]!r})" for f in unacknowledged_missing)
            + f"; raw headers are {raw_headers}. Pin the spelling with --header-map, or if "
            "the field is genuinely not part of this report, add it to ACKNOWLEDGED_ABSENT "
            "with a reason — a mapped header never degrades to a silent empty column."
        )
    acknowledged_absent = tuple(f for f in ACKNOWLEDGED_ABSENT if hmap[f] not in present)
    mapped_headers = {hmap[f] for f in hmap if hmap[f] in present}
    dropped = tuple(h for h in raw_headers if h in KNOWN_DROPPED and h not in mapped_headers)
    unknown = tuple(h for h in raw_headers if h not in mapped_headers and h not in KNOWN_DROPPED)

    def get(row: dict[str, str], logical: str) -> str:
        header = hmap[logical]
        return (row.get(header) or "").strip() if header in present else ""

    dev_teams: list[dict[str, str]] = []
    mappings: list[dict[str, str]] = []
    seen_teams: set[str] = set()
    report = ProjectionReport(
        raw_rows=len(raw_rows),
        raw_headers=tuple(raw_headers),
        acknowledged_absent=acknowledged_absent,
        unknown_headers=unknown,
        dropped_by_design=dropped,
        header_map=dict(hmap),
    )
    for row in raw_rows:
        team_id = get(row, "team_id")
        product_id = get(row, "product_id")
        if _blank(team_id) or _blank(product_id):
            report.skipped_no_key += 1
            continue
        team_type = get(row, "relationship_type").lower()
        if team_type not in _VALID_TEAM_TYPES:
            report.unrecognised_team_type += 1
        if team_id not in seen_teams:
            # one DevTeam row per team; the report is one row per team, but a
            # re-export that repeats a team must not MERGE it twice here
            seen_teams.add(team_id)
            dev_teams.append(
                {
                    "team_id": team_id,
                    "name": get(row, "team_name"),
                    "jira_board_id": get(row, "jira_board_id"),
                    "parent_product_id": product_id,
                }
            )
        sponsored_product = get(row, "sponsoring_product_id")
        sponsored_area = get(row, "sponsoring_area_product_id")
        mappings.append(
            {
                "team_id": team_id,
                "product_id": product_id,
                "area_product_id": get(row, "supporting_area_product_id"),
                # the row model normalises ';' -> ',' at the boundary; pass verbatim
                "seal_ids": get(row, "seal_ids"),
                "team_type": team_type,
                "sponsored": "true" if (sponsored_product or sponsored_area) else "false",
                "sponsored_product_id": sponsored_product,
                "sponsored_area_product_id": sponsored_area,
            }
        )
    report.dev_team_rows = len(dev_teams)
    report.mapping_rows = len(mappings)
    return dev_teams, mappings, report


def project_team_report(
    raw_csv: str | Path,
    out_dir: str | Path,
    header_map: dict[str, str] | None = None,
) -> ProjectionReport:
    """Read the raw report, write the two loader files into ``out_dir``."""
    raw_path = Path(raw_csv)
    with raw_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        headers = list(reader.fieldnames or [])
        rows = list(reader)
    dev_teams, mappings, report = project_rows(rows, headers, header_map)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    _write(out / DEV_TEAMS_FILE, DEV_TEAMS_COLUMNS, dev_teams)
    _write(out / PAT_PRODUCT_MAPPING_FILE, PAT_PRODUCT_MAPPING_COLUMNS, mappings)
    return report


def _write(path: Path, columns: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})
