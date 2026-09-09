"""Render the long-form SDLC Application Run Book for one Control-M folder.

Usage (from the repo root)::

    # the clone-reproducible path — reads the bundled sample CSVs, no venue
    poetry run python .claude/skills/controlm-runbook-automation-SDLC/generate_runbook.py \\
        --folder PRARAG-HLDM-70002-PEX-RFND-DLY --out /tmp/runbook.md

    # the real path — reads the DryDocs graph
    poetry run python .claude/skills/controlm-runbook-automation-SDLC/generate_runbook.py \\
        --folder PRARAG-HLDM-70002-PEX-RFND-DLY --source graph --database z8demo \\
        --out /tmp/runbook.md

    # what the graph could answer for a folder, without writing a document
    ... --folder <name> --coverage-only

WHAT THIS IS. The `-excel` sibling emits the MINIMUM VIABLE runbook — a 2-tab
folder-grain workbook support teams exchange. This one emits the LONG FORM: the
Tier 2/Tier 3 SDLC Run Book whose canonical shape is
`docs/design/templates/sdlc-app-runbook.outline.yaml`. Same folder, same graph,
two audiences.

THREE FILES, THREE JOBS, AND THE SPLIT IS THE POINT.

  * the OUTLINE (`docs/design/templates/sdlc-app-runbook.outline.yaml`) owns the
    section set, the order, the headings and what each section must contain. It
    is the doc-type contract and it is not this skill's to change.
  * `section-spec.yaml` owns provenance: for each of those sections, can the
    graph supply it (`graph`), partly supply it (`graph-partial`), or not at all
    (`manual`)? That vocabulary is the `-excel` sibling's, verbatim, so the two
    skills cannot end up with two names for one concept.
  * this file owns rendering, and NOTHING ELSE. It never decides what a section
    is called or whether the graph can answer it — it reads both from the files
    above. A section added to the outline fails the spec test until it is
    labeled here, which is the drift guard working rather than a nuisance.

WHY TWO FACT SOURCES. The acceptance for this skill asks for generation "from
the graph", proven by "a document generated for a sample folder". Those pull in
opposite directions: a live graph is the real path, and a live graph is exactly
what a fresh clone does not have. So the loaders produce the SAME
:class:`FolderFacts` from either side — the bundled CSVs under
`drydocs/data/samples/` (no Neo4j, no `DRYDOCS_DATA_ROOT`, works in any clone)
or the graph itself. The renderer cannot tell them apart, and every generated
document names which one it came from on its cover. The unit test uses the
sample path so the proof reproduces anywhere; the graph path is exercised
against a bundled-samples database and the run book records the venue.

NO CLOCK. Nothing here calls `datetime.now()`. The cover's date is the newest
`capture_date` in the folder's own fact bundle — the date the DATA reflects,
which is the honest answer and is also the reason two runs over one bundle are
byte-identical. A generated artifact that changes because it was generated
twice is an artifact nothing can guard.

WHAT IT REFUSES TO INVENT. A `manual` section gets its table shape, its column
headers and an explicit capture marker — never a plausible-looking filled row.
A `graph-partial` section fills the columns the graph answers and writes an
explicit unknown in the ones it does not. The whole value of a run book is that
a Tier 2 engineer at 03:00 can trust what it says; a fabricated retention
period or a condition name presented as a trigger-file path is worse than a
blank, because a blank is visibly a blank.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

from drydocs.cli_shared import DEFAULT_SAMPLES_DIR  # noqa: E402
from drydocs_core.adapters.csv_adapter import CsvAdapter  # noqa: E402
from drydocs_core.entity_extract import extract_entities  # noqa: E402
from drydocs_core.orchestration.controlm import (  # noqa: E402
    ParsedFolderName,
    parse_command,
    parse_folder_name,
)
from drydocs_core.orchestration.shell import Invocation  # noqa: E402

HERE = Path(__file__).parent
SPEC_PATH = HERE / "section-spec.yaml"
OUTLINE_PATH = REPO / "docs" / "design" / "templates" / "sdlc-app-runbook.outline.yaml"

#: The bundled sample directory, taken from the CLI's own constant rather than
#: rebuilt from the repo root. That constant is `__file__`-anchored on purpose —
#: an installed wheel has no checkout to follow — and there is a SECOND constant
#: of the same name in `drydocs.seal_samples` which is a build script's WRITE
#: target. This is the read-side one.
SAMPLES_DIR = DEFAULT_SAMPLES_DIR

#: The two SEAL sample files are NOT tracked: `.gitignore` ignores `drydocs/data/`
#: and the 15 sample files that ship are force-added exceptions, which these two
#: are not — they are regenerated per machine by `scripts/build_seal_samples.py`.
#: So a fresh clone has the Control-M samples and no ownership data at all. The
#: loader treats them as optional and the coverage report says which way it went;
#: a generator that assumed they ship would work on the machine that built it and
#: fail everywhere else, which is the worst kind of working.
OPTIONAL_SAMPLES = ("seal_application_data__sample.csv", "seal_contact_data__sample.csv")

#: What the spec's three `source:` values mean in the generated document. The
#: left column is the `-excel` sibling's vocabulary; the right is the wording the
#: backlog item asked for. One concept, one machine-readable name, both labels
#: visible to a reader who only has the rendered document.
PROVENANCE_LABELS = {
    "graph": "GRAPH-DERIVED",
    "graph-partial": "GRAPH-DERIVED (partial) + SME-RESIDUE",
    "manual": "SME-RESIDUE",
}

#: Written into a cell the graph was asked for and could not answer. One token,
#: so a reader scanning a filled book can see the gaps and a script can count
#: them. Distinct from an EMPTY cell, which means the section never asks.
UNKNOWN = "_not captured_"

#: Written into a `manual` section's table body: the shape is right, the rows
#: are the SME's to supply.
CAPTURE_ROW_NOTE = "_SME capture — no ingested system of record; see the marker above._"

#: Parameter-file extensions, used ONLY to pick a parameter file out of an
#: invocation's arguments when the parser did not identify a config path itself.
#: The invocation KIND comes from the parser, never from a suffix.
PARAM_SUFFIXES = (".pset", ".prm", ".param", ".parm")


@dataclass
class CommandFact:
    """One launched artifact, with every job in this folder that launches it.

    Keyed on the parser's ``target`` rather than on the raw command line, so one
    wrapper script called by four jobs with four argument sets is ONE row with
    four callers — the fan-out the folder-set profiler measures — instead of four
    rows that look like four different scripts.
    """

    target: str
    kind: str
    config_path: str | None
    raw: str
    jobs: list[str] = field(default_factory=list)


def _parameter_file(inv: Invocation) -> str | None:
    """The parameter file this invocation uses, if it names one.

    The parser's ``config_path`` first — it is the field that answers the
    question. Falling back to the target and then the arguments covers the two
    shapes the bundled sample and the sibling's own example use: a parameter set
    invoked directly, and one passed as an argument to a wrapper script.
    """
    if inv.config_path:
        return inv.config_path
    if inv.target.endswith(PARAM_SUFFIXES):
        return inv.target
    for arg in inv.args:
        if arg.endswith(PARAM_SUFFIXES):
            return arg
    return None


# --------------------------------------------------------------------------
# facts
# --------------------------------------------------------------------------


@dataclass
class FolderFacts:
    """Everything the renderer is allowed to know about one Control-M folder.

    Both loaders build this and nothing else, so the renderer cannot acquire a
    dependency on where the facts came from. ``provenance`` and ``venue`` are
    carried for the cover, never read by a section renderer.
    """

    folder_name: str
    folder: dict[str, str] = field(default_factory=dict)
    jobs: list[dict[str, str]] = field(default_factory=list)
    conditions_in: list[dict[str, str]] = field(default_factory=list)
    conditions_out: list[dict[str, str]] = field(default_factory=list)
    application: dict[str, str] | None = None
    app_id_origin: str = "none"
    contacts: list[dict[str, str]] = field(default_factory=list)
    hosts: list[str] = field(default_factory=list)
    server: str = ""
    #: condition name -> (folder that emits it, job that emits it). Built across
    #: the WHOLE estate, not just this folder: the bundled sample's own shape
    #: shows why — every one of the refund folder's seven IN conditions is raised
    #: by a job in a DIFFERENT folder, so a folder-scoped lookup would report all
    #: seven as "external" and the most useful sentence in the run book ("this
    #: waits on that job over there") would never be written.
    emitters: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    #: condition name -> the (folder, job) pairs that WAIT on it, estate-wide. The
    #: mirror of `emitters`, and the one fact in this whole document that answers
    #: "if this folder is late, who else is late" — the question a support
    #: engineer actually has at 03:00. Nothing else here can answer it, because
    #: every other section looks inward at one folder.
    consumers: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    provenance: str = ""
    venue: str = ""
    missing_inputs: list[str] = field(default_factory=list)

    @property
    def parsed_name(self) -> ParsedFolderName:
        return parse_folder_name(self.folder_name)

    @property
    def capture_date(self) -> str:
        """The newest capture date across the bundle — the cover's Date.

        Deterministic by construction: it is a property of the DATA, so the same
        bundle renders the same document however many times it is run.
        """
        stamps = [row.get("capture_date", "") for row in [self.folder, *self.jobs]]
        stamps = [str(s)[:10] for s in stamps if s]
        return max(stamps) if stamps else UNKNOWN

    def commands(self) -> list[CommandFact]:
        """What each job actually LAUNCHES, through the repo's own command parser.

        Not a string slice of `cmd_line`. `drydocs_core.orchestration.controlm`
        exports `parse_command`, the same parser the folder-set profiler and the
        lineage inventory extractor use, and it is the reason this run book and
        the `-excel` workbook cannot print different script paths for one folder.

        Slicing the raw string agrees with the parser on the bundled sample only
        because every sample command line is a bare path with no arguments. At
        production shapes it stops agreeing, in four ways at once, and every one
        of them is a wrong value in a column a reader trusts:

            sh /path/run_wrapper.ksh pex_calctot.pset {ODATE},1,Y,NO
            java -jar /apps/.../dt-launcher-current.jar -c /apps/.../conf.json

        the whole argv would be printed as the script name; the shell verb would
        become part of the "scripts location" directory; one wrapper invoked by
        two jobs would render as two different scripts rather than one with two
        callers; and the parameter file would be buried in the argv instead of
        landing in the row named for it. The parser answers all four —
        `target`, `config_path`, `invocation_type` — so this reads the parser.
        """
        by_target: dict[str, CommandFact] = {}
        for job in self.jobs:
            raw = (job.get("cmd_line") or "").strip()
            if not raw:
                continue
            job_name = job.get("job_name", "")
            parsed = parse_command(raw)
            if not parsed.invocations:
                # Nothing the parser recognized. Reported, never dropped.
                fact = by_target.setdefault(
                    raw, CommandFact(target=raw, kind="UNPARSED", config_path=None, raw=raw)
                )
                if job_name not in fact.jobs:
                    fact.jobs.append(job_name)
                continue
            for inv in parsed.invocations:
                fact = by_target.setdefault(
                    inv.target,
                    CommandFact(
                        target=inv.target,
                        kind=inv.invocation_type,
                        config_path=_parameter_file(inv),
                        raw=raw,
                    ),
                )
                if job_name not in fact.jobs:
                    fact.jobs.append(job_name)
        for fact in by_target.values():
            fact.jobs.sort()
        return sorted(by_target.values(), key=lambda f: f.target)

    def shell_scripts(self) -> list[CommandFact]:
        """The SHELL SCRIPT launches. Section 6.3's subject, and only that.

        The outline asks 6.3 for "every .ksh invoked from Informatica workflows or
        Control-M". A Control-M command line is not always a script: measured on
        the bundled sample, 10 of the 16 distinct command lines are Informatica
        parameter sets and 6 are shell scripts. The classification is the parser's
        `invocation_type`, not a suffix test, so a wrapper invoked as
        `sh /path/x.ksh ...` classifies correctly and a `.ksh` argument to
        something else does not.
        """
        return [fact for fact in self.commands() if fact.kind == "SHELL_SCRIPT"]

    def non_shell_commands(self) -> list[CommandFact]:
        """Everything else the folder launches, kept so nothing is dropped."""
        return [fact for fact in self.commands() if fact.kind != "SHELL_SCRIPT"]

    def script_directories(self) -> list[str]:
        """The directories the launched artifacts live in — parents of TARGETS.

        Of the target, never of the raw command line: `Path(raw).parent` on
        `sh /home/x/run.ksh a b` yields `sh /home/x`, which is presented to a
        reader as a directory and is not one.
        """
        dirs = {
            PurePosixPath(fact.target).parent.as_posix()
            for fact in self.commands()
            if fact.target.startswith("/")
        }
        return sorted(dirs)

    def conditions_for(self, job_id: str) -> list[dict[str, str]]:
        """This job's IN conditions, ordered as Control-M orders them.

        Sorted by ``order_`` where the source carries it, so the AND/OR sequence
        a reader sees matches the sequence the scheduler evaluates.
        """
        rows = [c for c in self.conditions_in if str(c.get("job_id")) == str(job_id)]
        return sorted(rows, key=lambda c: (int(c.get("order_") or 0), c.get("condition_name", "")))

    def emitted_by(self, condition_name: str) -> str:
        """EVERY job that raises ``condition_name``, or '' if nothing here does.

        Plural on purpose. One condition name can be raised by several jobs — in
        the bundled sample, ``PL-PARAD0010_..._DAT_ONPM_FW-OK`` is raised from two
        different folders — and naming only the first would tell a reader chasing
        a late upstream to go look at the wrong job. Whichever emitter actually
        ran late, the run book has to list them all.
        """
        raising = self.emitters.get(condition_name) or []
        if not raising:
            return ""
        return " or ".join(
            job if folder == self.folder_name else f"{job} in `{folder}`" for folder, job in raising
        )


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Rows from one sample CSV, through the repo's own adapter.

    ``CsvAdapter`` handles the BOM, lowercases headers and turns an empty cell
    into ``""`` rather than ``None`` — three behaviours a second reader here
    would have to reproduce and would eventually get wrong. Returns ``[]`` for a
    file that is not present: see ``OPTIONAL_SAMPLES``.
    """
    if not path.exists():
        return []
    with CsvAdapter(path) as adapter:
        return list(adapter.rows())


def _app_id_from_folder_name(folder_name: str) -> str:
    """The application id the folder name carries, via the shared extractor.

    Reuses ``drydocs_core.entity_extract`` rather than a local regex: that module
    already owns the measured 5-to-7-digit width rule and the overlap handling
    that keeps a folder name's issue-key-shaped substring from being read as an
    id. A second regex here would be a second answer to a settled question.
    """
    for match in extract_entities(folder_name):
        if match.kind == "application_id":
            return match.value
    return ""


def load_from_samples(folder_name: str, samples_dir: Path = SAMPLES_DIR) -> FolderFacts:
    """Build the bundle from the committed sample CSVs. No graph, no data root."""
    folders = _read_csv(samples_dir / "controlm_folders__sample.csv")
    folder = next((f for f in folders if f.get("sched_table") == folder_name), None)
    if folder is None:
        known = sorted(f.get("sched_table", "") for f in folders)
        raise SystemExit(
            f"no sample folder named {folder_name!r}. The bundled folders are:\n  "
            + "\n  ".join(known)
        )
    folder_id = folder["folder_id"]

    jobs = [
        j
        for j in _read_csv(samples_dir / "controlm_jobs__sample.csv")
        if j.get("folder_id") == folder_id and j.get("is_current_version") == "Y"
    ]
    jobs.sort(key=lambda j: (int(j.get("job_order") or 0), j.get("job_id", "")))

    all_in = _read_csv(samples_dir / "controlm_conditions_in__sample.csv")
    all_out = _read_csv(samples_dir / "controlm_conditions_out__sample.csv")
    cond_in = [c for c in all_in if c.get("folder_id") == folder_id]
    cond_out = [c for c in all_out if c.get("folder_id") == folder_id]

    # Estate-wide, so a cross-folder emitter can be named. See FolderFacts.emitters.
    all_jobs = _read_csv(samples_dir / "controlm_jobs__sample.csv")
    job_by_key = {(j.get("folder_id"), j.get("job_id")): j for j in all_jobs}
    folder_by_id = {f["folder_id"]: f.get("sched_table", "") for f in folders}
    emitters: dict[str, list[tuple[str, str]]] = {}
    for cond in all_out:
        job = job_by_key.get((cond.get("folder_id"), cond.get("job_id")))
        if job:
            pair = (folder_by_id.get(cond.get("folder_id", ""), ""), job.get("job_name", ""))
            raising = emitters.setdefault(cond.get("condition_name", ""), [])
            if pair not in raising:
                raising.append(pair)
    for raising in emitters.values():
        raising.sort()

    consumers: dict[str, list[tuple[str, str]]] = {}
    for cond in all_in:
        job = job_by_key.get((cond.get("folder_id"), cond.get("job_id")))
        if job:
            pair = (folder_by_id.get(cond.get("folder_id", ""), ""), job.get("job_name", ""))
            waiting = consumers.setdefault(cond.get("condition_name", ""), [])
            if pair not in waiting:
                waiting.append(pair)
    for waiting in consumers.values():
        waiting.sort()

    app_id = _app_id_from_folder_name(folder_name)
    application = None
    origin = "none — the folder name carries no application-id segment"
    contacts: list[dict[str, str]] = []
    missing = [n for n in OPTIONAL_SAMPLES if not (samples_dir / n).exists()]
    if app_id:
        rows = _read_csv(samples_dir / "seal_application_data__sample.csv")
        application = next((a for a in rows if a.get("app_id") == app_id), None)
        if application:
            origin = (
                f"folder-name segment {app_id}, matched in the SEAL sample "
                "(a CSV bundle has no attribution edge to confirm it)"
            )
        elif missing:
            origin = (
                f"folder name carries {app_id}; the SEAL sample files are absent "
                "from this checkout, so ownership is unresolved"
            )
        else:
            origin = f"folder name carries {app_id}, which has no row in the SEAL sample"
        contacts = [
            {
                "role": c.get("role_name", ""),
                "name": c.get("employee_name", ""),
                "employee_id": c.get("employee_sid", ""),
                "email": c.get("employee_email", ""),
            }
            for c in _read_csv(samples_dir / "seal_contact_data__sample.csv")
            if c.get("app_id") == app_id
        ]
        contacts.sort(key=lambda c: (c["role"], c["name"]))

    hosts = sorted({j.get("node_id", "") for j in jobs if j.get("node_id")})
    rel = (
        samples_dir.relative_to(REPO).as_posix() if samples_dir.is_relative_to(REPO) else "samples"
    )
    return FolderFacts(
        folder_name=folder_name,
        folder=folder,
        jobs=jobs,
        conditions_in=cond_in,
        conditions_out=cond_out,
        application=application,
        app_id_origin=origin,
        contacts=contacts,
        hosts=hosts,
        server=folder.get("data_center", ""),
        emitters=emitters,
        consumers=consumers,
        provenance=f"bundled sample CSVs ({rel})",
        venue="none - the Control-M samples are tracked and read the same in any clone",
        missing_inputs=missing,
    )


FOLDER_QUERY = """
MATCH (f:ControlMFolder {sched_table: $folder})
OPTIONAL MATCH (f)-[:SCHEDULED_ON]->(srv:ControlMServer)
RETURN properties(f) AS folder, srv.name AS server
"""

JOBS_QUERY = """
MATCH (f:ControlMFolder {sched_table: $folder})-[:CONTAINS_JOB]->(j:ControlMJob)
RETURN properties(j) AS job
"""

# The condition's name lives on `Condition.name`, and the AND/OR plus evaluation
# order live on the REQUIRES_IN_CONDITION RELATIONSHIP — not on the node, and not
# under the CSV's `condition_name` header. Reading `c.condition_name` here returns
# null for every row and the section renders empty with no error, which is why
# these property names were read off the live schema rather than transcribed from
# the sample header.
CONDITIONS_IN_QUERY = """
MATCH (f:ControlMFolder {sched_table: $folder})-[:CONTAINS_JOB]->(j:ControlMJob)
MATCH (j)-[e:REQUIRES_IN_CONDITION]->(c:Condition)
RETURN j.job_id AS job_id, c.name AS condition_name,
       e.and_or AS and_or, e.order_ AS order_
"""

CONDITIONS_OUT_QUERY = """
MATCH (f:ControlMFolder {sched_table: $folder})-[:CONTAINS_JOB]->(j:ControlMJob)
MATCH (j)-[:EMITS_OUT_CONDITION]->(c:Condition)
RETURN j.job_id AS job_id, c.name AS condition_name
"""

# Estate-wide, so a cross-folder emitter can be named rather than reported as
# "external". Scoped to the conditions this folder actually waits on.
#
# THE JOIN IS ON THE NAME, NOT ON THE NODE, and that is the whole correctness of
# these two queries. `constraints.cypher` declares
#     REQUIRE (c.folder_id, c.name) IS NODE KEY
# so a :Condition node is PER FOLDER by design: one condition name that crosses
# folders exists as several distinct nodes. Measured on the bundled estate, the
# name `PL-PARAD0010_PEX_EXPLOANRQTDTL_DAT_ONPM_FW-OK` is three nodes in three
# folders. A pattern that matches the waiter's node and the emitter's node as the
# SAME `c` therefore resolves only same-folder pairs — it returns zero rows for
# exactly the cross-folder case these queries exist to answer, and the document
# then tells a Tier 2 engineer that an upstream is outside the estate while the
# graph holds the emitting job and folder. That is the quietly-wrong run book
# this skill is supposed to prevent, so the join reads the name.
EMITTERS_QUERY = """
MATCH (target:ControlMFolder {sched_table: $folder})-[:CONTAINS_JOB]->(tj:ControlMJob)
MATCH (tj)-[:REQUIRES_IN_CONDITION]->(cin:Condition)
MATCH (src:ControlMFolder)-[:CONTAINS_JOB]->(sj:ControlMJob)-[:EMITS_OUT_CONDITION]->(cout:Condition)
WHERE cout.name = cin.name
RETURN DISTINCT cin.name AS condition_name, src.sched_table AS folder, sj.job_name AS job
"""

# The mirror: who WAITS on what this folder emits. The blast radius. Same
# name-join rule, same reason.
CONSUMERS_QUERY = """
MATCH (target:ControlMFolder {sched_table: $folder})-[:CONTAINS_JOB]->(tj:ControlMJob)
MATCH (tj)-[:EMITS_OUT_CONDITION]->(cout:Condition)
MATCH (dst:ControlMFolder)-[:CONTAINS_JOB]->(dj:ControlMJob)-[:REQUIRES_IN_CONDITION]->(cin:Condition)
WHERE cin.name = cout.name
RETURN DISTINCT cout.name AS condition_name, dst.sched_table AS folder, dj.job_name AS job
"""

# The attribution edge lands on the application's BATCH PORT, never on the
# application node and never on a job — the folder-grain ruling. Reading it any
# other way finds nothing and quietly reports the folder as unattributed.
APPLICATION_QUERY = """
MATCH (f:ControlMFolder {sched_table: $folder})-[:BELONGS_TO_APPLICATION]->(p:Port)
MATCH (a:BusinessApplication {app_id: p.parent_app_id})
RETURN properties(a) AS app, p.active_state AS port_state
"""

# The HAD_ROLE target is NOT constrained to a label. The role vocabulary's nodes
# carry `:TOMRole`, and a `:Role` there matches nothing — every contact then
# renders as "unlabeled role", which is not an error anywhere, just twelve
# identical-looking rows in the one table an escalation is routed from. A second
# guessed label after `Condition.condition_name`; both were caught by comparing
# the graph path's output against the samples path's, which is the reason the two
# paths render the same structure.
CONTACTS_QUERY = """
MATCH (a:BusinessApplication {app_id: $app_id})-[:QUALIFIED_ATTRIBUTION]->(at:Attribution)
MATCH (at)-[:HAS_AGENT]->(e:Employee)
OPTIONAL MATCH (at)-[:HAD_ROLE]->(r)
RETURN coalesce(r.pref_label, r.id, 'unlabeled role') AS role,
       e.full_name AS name, e.employee_id AS employee_id, e.email AS email
"""

# RUNS_ON lands on either a :ControlMHostGroup (which carries `name`) or an
# :ExecutionHost (which carries `nodeid`) — two labels, two property names, read
# off the live schema. `j.node_id` is the fallback for a job whose host row was
# never ingested, which is the common case in the bundled sample.
HOSTS_QUERY = """
MATCH (f:ControlMFolder {sched_table: $folder})-[:CONTAINS_JOB]->(j:ControlMJob)
OPTIONAL MATCH (j)-[:RUNS_ON]->(h)
RETURN collect(DISTINCT coalesce(h.name, h.nodeid, j.node_id)) AS hosts
"""


def load_from_graph(client, folder_name: str, venue: str) -> FolderFacts:
    """Build the same bundle from the graph. ``client`` is a ``Neo4jClient``."""
    head = client.run(FOLDER_QUERY, {"folder": folder_name})
    if not head:
        raise SystemExit(f"no :ControlMFolder with sched_table={folder_name!r} in {venue}")
    folder = dict(head[0]["folder"])
    server = head[0].get("server") or ""

    jobs = [dict(row["job"]) for row in client.run(JOBS_QUERY, {"folder": folder_name})]
    jobs.sort(key=lambda j: (int(j.get("job_order") or 0), str(j.get("job_id", ""))))

    cond_in = [
        {
            "job_id": str(row["job_id"]),
            "condition_name": row["condition_name"] or "",
            "and_or": row["and_or"] or "",
            "order_": str(row["order_"] or 0),
        }
        for row in client.run(CONDITIONS_IN_QUERY, {"folder": folder_name})
    ]
    cond_in.sort(key=lambda c: (c["job_id"], int(c["order_"]), c["condition_name"]))
    cond_out = [
        {"job_id": str(row["job_id"]), "condition_name": row["condition_name"] or ""}
        for row in client.run(CONDITIONS_OUT_QUERY, {"folder": folder_name})
    ]
    cond_out.sort(key=lambda c: (c["job_id"], c["condition_name"]))

    emitters: dict[str, list[tuple[str, str]]] = {}
    for row in client.run(EMITTERS_QUERY, {"folder": folder_name}):
        pair = (row["folder"] or "", row["job"] or "")
        raising = emitters.setdefault(row["condition_name"], [])
        if pair not in raising:
            raising.append(pair)
    for raising in emitters.values():
        raising.sort()

    consumers: dict[str, list[tuple[str, str]]] = {}
    for row in client.run(CONSUMERS_QUERY, {"folder": folder_name}):
        pair = (row["folder"] or "", row["job"] or "")
        waiting = consumers.setdefault(row["condition_name"], [])
        if pair not in waiting:
            waiting.append(pair)
    for waiting in consumers.values():
        waiting.sort()

    application = None
    origin = "none"
    app_rows = client.run(APPLICATION_QUERY, {"folder": folder_name})
    if app_rows:
        application = dict(app_rows[0]["app"])
        origin = f"BELONGS_TO_APPLICATION -> batch port ({app_rows[0].get('port_state')})"
    else:
        # No confirmed edge. Fall back to the id the folder NAME carries, and say
        # so — an unconfirmed attribution presented as a confirmed one is the
        # single most misleading thing a generated run book could do.
        app_id = _app_id_from_folder_name(folder_name)
        if app_id:
            rows = client.run(
                "MATCH (a:BusinessApplication {app_id: $app_id}) RETURN properties(a) AS app",
                {"app_id": app_id},
            )
            if rows:
                application = dict(rows[0]["app"])
                origin = "folder-name segment — NO attribution edge in the graph"
            else:
                origin = f"folder name carries {app_id}, which has no :BusinessApplication node"

    contacts: list[dict[str, str]] = []
    if application and application.get("app_id"):
        contacts = [
            {
                "role": row["role"] or "",
                "name": row["name"] or "",
                "employee_id": row["employee_id"] or "",
                "email": row["email"] or "",
            }
            for row in client.run(CONTACTS_QUERY, {"app_id": application["app_id"]})
        ]
        contacts.sort(key=lambda c: (c["role"], c["name"]))

    host_rows = client.run(HOSTS_QUERY, {"folder": folder_name})
    hosts = sorted({h for h in (host_rows[0]["hosts"] if host_rows else []) if h})

    return FolderFacts(
        folder_name=folder_name,
        folder={k: str(v) for k, v in folder.items()},
        jobs=[{k: str(v) for k, v in job.items()} for job in jobs],
        conditions_in=cond_in,
        conditions_out=cond_out,
        application={k: str(v) for k, v in application.items()} if application else None,
        app_id_origin=origin,
        contacts=contacts,
        hosts=hosts,
        server=str(server),
        emitters=emitters,
        consumers=consumers,
        provenance="DryDocs graph",
        venue=venue,
    )


# --------------------------------------------------------------------------
# markdown helpers
# --------------------------------------------------------------------------


def _cell(value: object) -> str:
    """One table cell, made safe for a pipe table.

    Two characters end a markdown table when they arrive inside a value, and both
    reach here from real data: a literal ``|`` (Control-M command lines contain
    pipes) and a newline (the sibling spec already carries a multi-line example
    value, so a real extract will too). A newline is folded to a space rather than
    escaped — a cell cannot hold a line break in this table syntax, and silently
    truncating the row at the break would drop content a reader needs.
    """
    if value is None or value == "":
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", " ").replace("|", "\\|").strip()


def table(header: list[str], rows: list[list[str]]) -> str:
    """A pipe table. An empty ``rows`` still emits the header — the shape IS content."""
    out = ["| " + " | ".join(_cell(h) for h in header) + " |", "|" + "---|" * len(header)]
    for row in rows:
        out.append("| " + " | ".join(_cell(c) for c in row) + " |")
    return "\n".join(out)


def capture_table(header: list[str]) -> str:
    return table(header, []) + "\n\n" + CAPTURE_ROW_NOTE


# --------------------------------------------------------------------------
# section renderers — one per anchor, keyed by the spec's `fill:`
# --------------------------------------------------------------------------


def _scheduling_state(facts: FolderFacts) -> str:
    """Whether the folder is scheduling, from the ONE field whose meaning is settled.

    ``user_daily`` is documented in the typed model as the active-scheduling flag,
    null meaning inactive — quarantined, not dropped. That is a fact about the
    folder a support reader must not miss.
    """
    flag = (facts.folder.get("user_daily") or "").strip()
    if flag.upper() == "Y":
        return "yes"
    if not flag:
        return "**NO — this folder is not actively scheduled** (quarantined, not dropped)"
    return f"flag is `{flag}`, which is neither Y nor empty — check the folder in Control-M"


def _lifecycle_code(facts: FolderFacts) -> str:
    """The raw lifecycle code, WITHOUT inventing a meaning for the letter.

    ``table_status`` is a one-character code and the repo's own source mapping
    says "BMC definition still to confirm". Reading `R` as "retired" would be a
    guess wearing the clothes of a fact, in the section of a run book a reader
    trusts most. Print the code, name it as undefined, and let the reader ask.
    """
    code = (facts.folder.get("table_status") or "").strip()
    if not code:
        return UNKNOWN
    return f"`{code}` — the code's meaning is not defined in any source we hold"


def _inactive_banner(facts: FolderFacts) -> list[str]:
    """A cover warning when the folder is not scheduling. Empty otherwise."""
    if (facts.folder.get("user_daily") or "").strip().upper() == "Y":
        return []
    return [
        ">",
        "> **THIS FOLDER IS NOT ACTIVELY SCHEDULED.** Its active-scheduling flag is not set,",
        "> which the typed model documents as inactive — quarantined, not dropped. Treat every",
        "> procedure below as historical until someone confirms the folder's status in",
        "> Control-M itself.",
    ]


def _r_front_matter(spec: dict, facts: FolderFacts, meta: dict) -> str:
    app = facts.application or {}
    name = app.get("name") or facts.folder_name
    parsed = facts.parsed_name
    rows = [
        ["**Product/Application/System**", f"{name} ({app.get('app_id', UNKNOWN)})"],
        ["**Document**", "Run Book"],
        ["**Control-M folder**", f"`{facts.folder_name}`"],
        ["**Project**", meta.get("project") or UNKNOWN],
        ["**Date (source data captured)**", facts.capture_date],
        ["**Version**", meta.get("version", "0.1-generated")],
        # DryDocs' OWN vocabulary (config/classification.yaml: External /
        # Internal-Public / Internal), which is what the outline's cover asks
        # for. The SEAL record's `info_classification` is a DIFFERENT vocabulary
        # with values like "Highly Confidential"; printing it in this row would
        # put the source system's term in a field that names ours. It gets its
        # own row below, labeled as the source's word — the two-part rule the
        # business-application identity gate settled: identity neutral, evidence
        # keeps the source's term.
        ["**Classification**", meta.get("classification", "Internal")],
        ["**Information classification (SEAL)**", app.get("info_classification") or UNKNOWN],
        ["**Reflects**", meta.get("reflects") or UNKNOWN],
        ["**Environment**", parsed.environment or UNKNOWN],
        ["**Line of business**", parsed.lob or UNKNOWN],
        ["**Active scheduling**", _scheduling_state(facts)],
        ["**Folder lifecycle status code**", _lifecycle_code(facts)],
    ]
    banner = _inactive_banner(facts)
    return "\n".join(
        [
            f"# {name} — SDLC Application Run Book",
            "",
            "> **GENERATED DOCUMENT — NOT YET REVIEWED.** Produced by",
            "> `.claude/skills/controlm-runbook-automation-SDLC/generate_runbook.py` against",
            f"> **{facts.provenance}** (venue: {facts.venue}).",
            ">",
            "> Every section below carries a provenance marker. **GRAPH-DERIVED** content came",
            "> from the fact bundle named above and can be regenerated. **SME-RESIDUE** content",
            "> is a shape waiting for a person — the generator does not invent it, and a table",
            f"> whose body reads `{CAPTURE_ROW_NOTE.strip('_')}` has not been filled in yet.",
            ">",
            f"> A cell reading `{UNKNOWN}` means the graph was asked and had no answer. That is",
            "> different from an empty cell, which means the section does not ask.",
            ">",
            "> **A FILLED run book is Internal.** Move it to `internal/` or `internal-local/`",
            "> before adding real values; nothing under this skill directory may carry them.",
            *banner,
            "",
            table(["", ""], rows),
            "",
            "### Generation coverage",
            "",
            _coverage_table(facts, meta),
        ]
    )


def _coverage_table(facts: FolderFacts, meta: dict) -> str:
    counts = meta["counts"]
    rows = [
        ["Sections in the outline", str(counts["total"])],
        ["`graph` — GRAPH-DERIVED", str(counts["graph"])],
        ["`graph-partial` — part derived, part capture", str(counts["graph-partial"])],
        ["`manual` — SME-RESIDUE", str(counts["manual"])],
        ["of those, N/A for a pure-batch module", str(counts["na"])],
        ["**Table rows filled from this bundle**", f"**{meta['filled_rows']}**"],
        [
            "**Sections whose tables came back empty** (a shape awaiting capture)",
            f"**{meta['empty_table_sections']}**",
        ],
        ["Jobs in this folder's bundle", str(len(facts.jobs))],
        ["Distinct launched artifacts", str(len(facts.commands()))],
        ["IN / OUT conditions", f"{len(facts.conditions_in)} / {len(facts.conditions_out)}"],
        ["Ownership contacts resolved", str(len(facts.contacts))],
        ["Application attribution", facts.app_id_origin],
    ]
    if facts.missing_inputs:
        rows.append(["Inputs absent from this checkout", ", ".join(facts.missing_inputs)])
    return table(["Measure", "Value"], rows)


def _r_document_control(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return capture_table(spec["columns"])


def _r_change_history(spec: dict, facts: FolderFacts, meta: dict) -> str:
    row = [
        meta.get("version", "0.1-generated"),
        f"Generated from {facts.provenance}",
        "All",
        "generate_runbook.py",
        facts.capture_date,
    ]
    return "\n".join(
        [
            table(spec["columns"], [row]),
            "",
            "_Rows for earlier versions are history this generator did not witness; it never",
            "invents one. Carry an existing book's rows forward by hand._",
        ]
    )


def _r_purpose(spec: dict, facts: FolderFacts, meta: dict) -> str:
    app = facts.application or {}
    name = app.get("name") or facts.folder_name
    return (
        f"This document is the overall reference for the **{name}** batch process, scheduled "
        f"in Control-M folder `{facts.folder_name}`. It serves the Tier 2 team for "
        "production-support activities; Tier 3 uses it as the entry point to the design "
        "documents it links."
    )


def _r_target_audience(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return (
        "Tier 2 (production support) and Tier 3 (application engineering). Contacts for both "
        "are in **Production Support** below; the ownership table under **High-Level Project "
        "Technical Architecture** names the accountable roles.\n\n"
        "_Which tiers this application is actually covered by is a support-model fact — "
        "confirm it before the first review._"
    )


def _r_architecture_model(spec: dict, facts: FolderFacts, meta: dict) -> str:
    lines = [
        "_Diagram to be attached: source databases and schemas, the ETL hop(s), the target "
        "warehouse, file exchanges, and downstream consumers, with the environment named on "
        "every node._",
        "",
        "The schedule sub-diagrams this folder needs, one per batch stream:",
        "",
    ]
    lines.append(
        table(
            ["Batch stream", "Control-M folder", "Trigger job", "Jobs"],
            [
                [
                    facts.parsed_name.segments[-1] if facts.parsed_name.segments else UNKNOWN,
                    f"`{facts.folder_name}`",
                    facts.jobs[0].get("job_name", UNKNOWN) if facts.jobs else UNKNOWN,
                    str(len(facts.jobs)),
                ]
            ],
        )
    )
    return "\n".join(lines)


def _r_etl_process_overview(spec: dict, facts: FolderFacts, meta: dict) -> str:
    parsed = facts.parsed_name
    cadence = parsed.segments[-1] if parsed.segments else UNKNOWN
    cyclic = sum(1 for j in facts.jobs if (j.get("cyclic") or "").upper() == "Y")
    return "\n".join(
        [
            f"The **{facts.folder_name}** batch runs {len(facts.jobs)} scheduled job(s) on the "
            f"`{cadence}` cadence carried by the folder name "
            f"({parsed.folder_type or UNKNOWN}); {cyclic} of them are cyclic. "
            f"Which upstream systems feed it, and the link to the application's TDD, are "
            f"{UNKNOWN}.",
            "",
            "The ETL processing layers this document covers:",
            "",
            "(a) Schedule; (b) FTP/SFTP output files; (c) Archival and file management; "
            "(d) Informatica objects; (e) UNIX objects.",
        ]
    )


def _r_schedule(spec: dict, facts: FolderFacts, meta: dict) -> str:
    rows = []
    for job in facts.jobs:
        detail = []
        for wait in facts.conditions_for(job.get("job_id", "")):
            name = wait["condition_name"]
            emitter = facts.emitted_by(name)
            joiner = (wait.get("and_or") or "").upper()
            prefix = f"{joiner} " if joiner and detail else ""
            source = f"from {emitter}" if emitter else "external — no emitter in the estate"
            detail.append(f"{prefix}`{name}` ({source})")
        rows.append(
            [
                job.get("job_name", ""),
                "Workflow" if job.get("task_type") == "Job" else (job.get("task_type") or ""),
                UNKNOWN,
                "; ".join(detail) if detail else "no IN conditions",
            ]
        )
    return "\n".join(
        [
            table(spec["columns"], rows),
            "",
            "_**Schedule Time** is not in the Control-M definition tables this graph ingests; "
            "it arrives with the average-run and ODATE-SLO seams the `-excel` sibling marks "
            "graph-partial. The dependency column lists CONDITIONS, which are not trigger-file "
            "paths — the literal `.done` paths, the alert cadence while waiting, and the "
            "restart-after-window rule are SME capture._",
        ]
    )


def _r_archival(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return capture_table(spec["columns"])


def _r_end_to_end(spec: dict, facts: FolderFacts, meta: dict) -> str:
    """The umbrella, plus the two things only an estate-wide read can say.

    The subsections below all look INWARD at one folder. This section is the only
    place the run book can answer "what has to finish before we start" and "who is
    late if we are late", and both are derivable from the condition graph. A Tier 2
    engineer opens a run book at 03:00 with a failed job; the run order and the
    blast radius are the two things they need before anything else in the document
    is useful.
    """
    order_rows = []
    for job in facts.jobs:
        waits = facts.conditions_for(job.get("job_id", ""))
        upstream = []
        for wait in waits:
            emitter = facts.emitted_by(wait["condition_name"])
            upstream.append(emitter or f"`{wait['condition_name']}` (no emitter in the estate)")
        role = "terminal" if (job.get("end_folder") or "").upper() == "Y" else ""
        if not waits:
            role = ("entry point, " + role).strip(", ") if role else "entry point"
        order_rows.append(
            [
                str(job.get("job_order") or ""),
                job.get("job_name", ""),
                role or "intermediate",
                "; ".join(upstream) if upstream else "nothing — starts on its own schedule",
            ]
        )

    blast_rows = []
    for cond in facts.conditions_out:
        name = cond.get("condition_name", "")
        for folder, job in facts.consumers.get(name, []):
            if folder != facts.folder_name:
                blast_rows.append([f"`{name}`", f"`{folder}`", job])
    blast_rows.sort()

    parts = [
        f"This folder holds **{len(facts.jobs)} job(s)** and "
        f"**{len(facts.commands())} distinct launched artifact(s)**. The subsections below cover "
        "scheduled workflows, the adhoc workflows, the shell scripts they invoke, the servers "
        "they run on, how they obtain credentials, and where the authoritative Control-M "
        "definition lives.",
        "",
        "**Run order within this folder**",
        "",
        table(["Order", "Job", "Role", "Waits for"], order_rows),
        "",
        "**Downstream impact — what waits on this folder**",
        "",
    ]
    if blast_rows:
        parts += [
            table(["Condition raised here", "Waiting folder", "Waiting job"], blast_rows),
            "",
            "_If this folder is late, the jobs above are late. This is the blast radius the "
            "condition graph can prove; consumers outside Control-M (reports, extracts, "
            "downstream teams) are SME capture._",
        ]
    else:
        parts.append(
            "No job anywhere in the ingested estate waits on a condition this folder raises. "
            "That means no ORCHESTRATED consumer — it does not mean nothing depends on this "
            "data. Downstream reports, extracts and teams are SME capture."
        )
    return "\n".join(parts)


def _param_file_cell(facts: FolderFacts, job: dict[str, str]) -> str:
    """The Param File Path value for one job, from the shared parser's answer.

    The parser reports a `config_path` where the invocation names one; where it
    does not, the row says so rather than printing the whole command line under a
    label that claims it is a parameter file.
    """
    raw = (job.get("cmd_line") or "").strip()
    if not raw:
        return UNKNOWN
    named = [fact.config_path for fact in facts.commands() if job.get("job_name") in fact.jobs]
    found = sorted({path for path in named if path})
    if found:
        return ", ".join(f"`{path}`" for path in found)
    return f"{UNKNOWN} — the command line `{raw}` names no parameter file"


def _r_etl_jobs(spec: dict, facts: FolderFacts, meta: dict) -> str:
    parts: list[str] = []
    inventory = [
        [str(i), job.get("job_name", ""), job.get("description", "") or UNKNOWN]
        for i, job in enumerate(facts.jobs, start=1)
    ]
    parts += ["**Workflow inventory**", "", table(spec["inventory_columns"], inventory), ""]
    parts += [
        "**Newly added workflows this revision**",
        "",
        table([*spec["inventory_columns"], "Comments"], []),
        "",
        "_A generator cannot know which workflows are new to a REVISION; it has one snapshot, "
        "not two. Fill this at review time, or diff two generated runs._",
        "",
    ]
    for job in facts.jobs:
        header_values = {
            "Control-M job name": job.get("job_name", ""),
            "Schedule Information": UNKNOWN,
            # The outline mandates this row's LABEL, and a Control-M command line
            # is not always a parameter file. Print what it actually is rather
            # than letting the mandated label assert something about the value.
            "Param File Path": _param_file_cell(facts, job),
            "Src Schema/DB": UNKNOWN,
            "Stg Schema/DB": UNKNOWN,
            "Target Schema/DB": UNKNOWN,
            "Folder name": f"`{facts.folder_name}`",
            "Source Table": UNKNOWN,
            "Stage Table": UNKNOWN,
            "Target Table": UNKNOWN,
        }
        # The label-less two-column shape the committed example uses for this
        # block: bold row labels down the left, values on the right.
        parts += [
            f"#### {job.get('job_name', '')}",
            "",
            table(["", ""], [[f"**{k}**", header_values[k]] for k in spec["header_rows"]]),
            "",
            "Below is the description of each task in the workflow.",
            "",
        ]
        task_rows = [[job.get("job_name", ""), job.get("description", "") or UNKNOWN]]
        for wait in facts.conditions_for(job.get("job_id", "")):
            name = wait["condition_name"]
            emitter = facts.emitted_by(name)
            task_rows.append(
                [
                    f"event-wait: `{name}`",
                    f"waits on {emitter}" if emitter else "waits on a condition nothing here emits",
                ]
            )
        parts += [table(spec["task_columns"], task_rows), ""]
    parts.append(
        "_The source/stage/target schema and table grain is an Informatica mapping fact. "
        "Control-M schedules a workflow; it does not know what the workflow reads and writes. "
        "Those rows stay explicitly uncaptured rather than guessed. The Control-M workspace "
        "screenshot the outline asks for is an SME artifact._"
    )
    return "\n".join(parts)


def _r_etl_adhoc(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return "\n".join(
        [
            table(spec["columns"], []),
            "",
            "_The Control-M definition carries no on-demand flag: an adhoc workflow is one a "
            "person runs, and nothing in the scheduled estate distinguishes it. N/A until "
            "adhoc entries are declared for this application._",
        ]
    )


def _r_unix_scripts(spec: dict, facts: FolderFacts, meta: dict) -> str:
    rows = [
        [
            f"`{fact.target}`",
            UNKNOWN,
            "; ".join(fact.jobs) + " (scheduled in Control-M)",
        ]
        for fact in facts.shell_scripts()
    ]
    parts = [table(spec["columns"], rows)]
    if not rows:
        parts += [
            "",
            "No job in this folder launches a shell script — see the table below for what it "
            "does launch.",
        ]
    others = facts.non_shell_commands()
    if others:
        by_kind: dict[str, list[str]] = {}
        for fact in others:
            by_kind.setdefault(fact.kind, []).append(fact.target)
        parts += [
            "",
            "**Not shell scripts — what else this folder launches**",
            "",
            table(
                ["Launch kind", "Artifacts"],
                [
                    [kind, ", ".join(f"`{t}`" for t in sorted(targets))]
                    for kind, targets in sorted(by_kind.items())
                ],
            ),
            "",
            "_Classified by the shared command parser, not by file extension. They are listed "
            "here rather than dropped, and their parameter files appear as **Param File Path** "
            "in the per-workflow blocks of section 6.1 — a parameter set under 'Unix Script "
            "Name' would be a value in the wrong column._",
        ]
    parts += [
        "",
        "_A path is not a description. What each script DOES — and the taxonomy the outline "
        "asks for (environment setup, workflow wrappers, parameter-file generators, "
        "validators, archival, SFTP movers, trigger waits, mailers, status updates, "
        "mutual-exclusion checks) — is a reading of the script bodies, which this graph "
        "does not hold._",
    ]
    return "\n".join(parts)


def _r_unix_servers(spec: dict, facts: FolderFacts, meta: dict) -> str:
    rows = [[h, "Execution host", facts.parsed_name.environment or UNKNOWN] for h in facts.hosts]
    if facts.server:
        rows.append([facts.server, "Control-M server / data center", "—"])
    return "\n".join(
        [
            table(["Server", "Role", "Environment"], rows),
            "",
            "_The DNS alias and the per-environment physical/virtual split are infrastructure "
            "facts outside the orchestrator's definition tables._",
        ]
    )


def _r_password_scripts(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return "\n".join(
        [
            "**Vault function call per script**",
            "",
            table(spec["columns"], [[f"`{f.target}`", UNKNOWN] for f in facts.shell_scripts()]),
            "",
            "**Safe details**",
            "",
            capture_table(spec["safe_columns"]),
            "",
            "**Vaulted database accounts**",
            "",
            capture_table(spec["account_columns"]),
            "",
            "_This section records the function CALL a script makes and never a secret value. "
            "The provider status command, the provider log locations and the owning IAM contact "
            "are capture._",
        ]
    )


def _r_password_adhoc(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return capture_table(spec["columns"])


def _r_controlm_job_details(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return (
        "The authoritative per-job artifact for this folder is the 2-tab Excel runbook's "
        "**Control M Job details** tab, generated by the sibling skill at "
        "`.claude/skills/controlm-runbook-automation-excel/`. Generate it for "
        f"`{facts.folder_name}` and file it beside this document.\n\n"
        "This run book deliberately does NOT reproduce that tab's ~35 columns: the workbook is "
        "where the per-job definition lives, and two renderings of one fact are two things that "
        "can disagree."
    )


def _r_sla(spec: dict, facts: FolderFacts, meta: dict) -> str:
    cadence = facts.parsed_name.segments[-1] if facts.parsed_name.segments else UNKNOWN
    rows = [
        [
            (facts.application or {}).get("app_short_name") or facts.parsed_name.app_code or "",
            job.get("job_name", ""),
            "Cyclic" if (job.get("cyclic") or "").upper() == "Y" else cadence,
            UNKNOWN,
            UNKNOWN,
            UNKNOWN,
            UNKNOWN,
        ]
        for job in facts.jobs
    ]
    return "\n".join(
        [
            "**Upstream dependency SLAs this batch inherits:** " + UNKNOWN + ".",
            "",
            table(spec["columns"], rows),
            "",
            "_Expected start and end times and the SLA itself come from the average-run seam "
            "(gated) and the ODATE-SLO metadata plan — graph-partial in the `-excel` spec and "
            "graph-partial here. A sibling claiming more would be the two-skills-disagreeing "
            "failure._",
        ]
    )


def _r_architecture_contacts(spec: dict, facts: FolderFacts, meta: dict) -> str:
    app = facts.application or {}
    project = meta.get("project") or app.get("name") or facts.folder_name
    rows = [
        [project, c["name"], c["role"], c["email"] or UNKNOWN] for c in facts.contacts if c["name"]
    ]
    stack = [
        ["ETL engine", UNKNOWN],
        ["Orchestrator", "BMC Control-M"],
        ["Operating system", UNKNOWN],
        ["Database", UNKNOWN],
    ]
    body = [
        "**Tool stack**",
        "",
        table(["Layer", "Product / version"], stack),
        "",
        "**Ownership and contacts**",
        "",
        table(spec["columns"], rows),
    ]
    if not rows:
        body += [
            "",
            f"_No ownership rows: {facts.app_id_origin}. Resolve the folder's attribution "
            "before the first review — an unattributed run book cannot route an escalation._",
        ]
    else:
        body += [
            "",
            "_'Areas of Responsibility' is filled with the role holder's contact point; the "
            "SEAL record does not carry a free-text responsibility statement._",
        ]
    return "\n".join(body)


def _r_configuration_setup(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return (
        "The environment-setup subsections follow. Sections that do not apply to a pure-batch "
        "module keep their place and their number, marked N/A with the reason."
    )


def _r_database_server(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return "\n".join(
        [
            "**Database Server Setup** — " + UNKNOWN + ".",
            "",
            "**Creation & Setup of Database** — the per-environment connect descriptors "
            "(DEV/UAT/PROD hosts, ports and service names) and the access-request procedure "
            "are capture. Real descriptors are Internal and must not be written into a file "
            "under this skill directory; record them in the filed copy under `internal/`.",
        ]
    )


def _r_application_login_ids(spec: dict, facts: FolderFacts, meta: dict) -> str:
    app = facts.application or {}
    name = app.get("name") or facts.folder_name
    owners = sorted({j.get("owner", "") for j in facts.jobs if j.get("owner")})
    rows = [[name, "Control-M", owner] for owner in owners]
    return "\n".join(
        [
            table(spec["columns"], rows),
            "",
            "_Login ids on the other systems the application touches (databases, file "
            "transfer, cloud) are not in the orchestrator's tables. Retired accounts stay as "
            "struck-through rows; the generator never removes a row an author added._",
        ]
    )


def _r_directory_configuration(spec: dict, facts: FolderFacts, meta: dict) -> str:
    owners = sorted({j.get("owner", "") for j in facts.jobs if j.get("owner")})
    owner = owners[0] if len(owners) == 1 else (", ".join(owners) or UNKNOWN)
    dirs = facts.script_directories()
    rows = [["Scripts location", f"`{d}`", owner] for d in dirs]
    for component in (
        "ETL repository details",
        "Session log files",
        "Source files location",
        "Target files location",
        "Target FTP location",
        "Archive files location",
        "Script log files location",
    ):
        rows.append([component, UNKNOWN, UNKNOWN])
    return "\n".join(
        [
            table(spec["columns"], rows),
            "",
            "_Every row the outline asks for is present. A MISSING row would read as 'not "
            f"applicable'; a row reading `{UNKNOWN}` reads as 'not captured yet', and those "
            "are different answers._",
        ]
    )


def _r_recovery(spec: dict, facts: FolderFacts, meta: dict) -> str:
    rows = [
        [
            "1",
            "Orchestrator outage",
            "The Control-M server or agent was unavailable for the batch window",
            "Confirm the folder's jobs did not start, then follow the manual-start procedure "
            "and check the batch's completion marker before starting any workflow. "
            f"The procedure itself is {UNKNOWN}.",
        ]
    ]
    return "\n".join(
        [
            table(spec["columns"], rows),
            "",
            "_The orchestrator-outage row is the one category derivable from knowing this is a "
            "Control-M folder. Every other failure category, and all special-case recovery "
            "(same-day restart rules, multi-day missed-load recovery, the parameter-file "
            "override query, the hard cautions), is exactly the knowledge a run book exists to "
            "capture from people._",
        ]
    )


def _r_production_support(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return "The support playbook. Subsections follow."


def _r_alerts(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return "\n".join(
        [
            "Two alert classes:",
            "",
            "- **Threshold Alert** — the job did not start, or did not end, on time.",
            "- **Failure Alert** — the job hit an execution issue; fix or debug, then restart.",
            "",
            capture_table(spec["columns"]),
            "",
            "_Which alerts this application actually raises, and to whom, is the escalation-DB "
            "half that belongs to the `-excel` sibling and to SME capture._",
        ]
    )


def _r_job_monitoring(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return (
        f"How runs are watched — workflow monitor, SLA-deviation capture, on-call paging — is "
        f"{UNKNOWN}.\n\n"
        "**ETL Rejects.** Sessions configured to fail on first error stop the load rather than "
        "loading partial data; production support finds the root cause before any reload. The "
        f"configuration this application uses is {UNKNOWN}."
    )


def _r_tier2_escalation(spec: dict, facts: FolderFacts, meta: dict) -> str:
    rows = [
        [
            str(i),
            c["role"],
            c["email"] or UNKNOWN,
            f"SID {c['employee_id']}" if c["employee_id"] else "",
        ]
        for i, c in enumerate(facts.contacts, start=1)
    ]
    return "\n".join(
        [
            table(spec["columns"], rows),
            "",
            "_Escalation LEVEL is filled with the row's order, not with a ranking the graph "
            "carries: the role vocabulary knows role names, not an escalation ladder. Contact "
            "NUMBERS are not in the ownership record either — the column shows the contact "
            "point the graph has._",
            "",
            "**Guideline scenarios** — trigger-file-not-received-by-`<T>`, "
            "upstream-load-incomplete, and workflow-failure escalation, each with its alert "
            f"email template and the mailing lists to address: {UNKNOWN}. This is the run "
            "book's most valuable content and none of it is derivable.",
        ]
    )


def _r_server_database_support(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return capture_table(spec["columns"])


def _r_business_contact(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return capture_table(spec["columns"])


def _r_appendix(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return capture_table(spec["columns"])


def _r_na(spec: dict, facts: FolderFacts, meta: dict) -> str:
    return f"N/A — {spec['na_reason']}."


#: `fill:` in the spec -> the callable that renders that section. The spec test
#: asserts this mapping is total in both directions, so a section cannot be added
#: to the spec without a renderer, or a renderer left behind when a section goes.
RENDERERS = {
    "front_matter": _r_front_matter,
    "document_control": _r_document_control,
    "change_history": _r_change_history,
    "purpose": _r_purpose,
    "target_audience": _r_target_audience,
    "architecture_model": _r_architecture_model,
    "etl_process_overview": _r_etl_process_overview,
    "schedule": _r_schedule,
    "archival_file_management": _r_archival,
    "end_to_end_process": _r_end_to_end,
    "etl_jobs": _r_etl_jobs,
    "etl_adhoc_jobs": _r_etl_adhoc,
    "unix_shell_scripts": _r_unix_scripts,
    "unix_servers": _r_unix_servers,
    "password_retrieval_scripts": _r_password_scripts,
    "password_retrieval_adhoc": _r_password_adhoc,
    "controlm_job_details": _r_controlm_job_details,
    "service_level_agreement": _r_sla,
    "architecture_contacts": _r_architecture_contacts,
    "configuration_setup": _r_configuration_setup,
    "database_server": _r_database_server,
    "application_login_ids": _r_application_login_ids,
    "directory_configuration": _r_directory_configuration,
    "recovery_procedures": _r_recovery,
    "production_support": _r_production_support,
    "alerts": _r_alerts,
    "job_monitoring": _r_job_monitoring,
    "tier2_escalation": _r_tier2_escalation,
    "server_database_support": _r_server_database_support,
    "business_contact": _r_business_contact,
    "appendix": _r_appendix,
    "na_section": _r_na,
}


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------


def load_spec(path: Path = SPEC_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_outline_sections(path: Path = OUTLINE_PATH) -> list[dict]:
    """The outline's sections, flattened to (anchor, heading, number, level).

    Numbering reproduces the committed example: top-level sections after the
    cover run 1.0, 2.0, ... and subsections take <parent>.<n>. It is derived from
    the outline's ORDER, never stored, so inserting a section renumbers the rest
    the way a human editor would.
    """
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    flat: list[dict] = []
    top = 0
    for section in doc.get("sections") or []:
        anchor = section["anchor"]
        if anchor == "front-matter":
            flat.append({"anchor": anchor, "heading": section["heading"], "number": "", "level": 1})
            continue
        top += 1
        flat.append(
            {
                "anchor": anchor,
                "heading": section["heading"],
                "number": f"{top}.0",
                "level": 2,
            }
        )
        for i, sub in enumerate(section.get("subsections") or [], start=1):
            flat.append(
                {
                    "anchor": sub["anchor"],
                    "heading": sub["heading"],
                    "number": f"{top}.{i}",
                    "level": 3,
                }
            )
    return flat


def _counts(spec: dict) -> dict[str, int]:
    sections = spec["sections"]
    return {
        "total": len(sections),
        "graph": sum(1 for s in sections if s["source"] == "graph"),
        "graph-partial": sum(1 for s in sections if s["source"] == "graph-partial"),
        "manual": sum(1 for s in sections if s["source"] == "manual"),
        "na": sum(1 for s in sections if s.get("na_for_batch")),
    }


def _marker(entry: dict) -> str:
    """The provenance line under a heading: the label plus what falls on each side."""
    label = PROVENANCE_LABELS[entry["source"]]
    bits = [f"> **{label}**"]
    if entry.get("derived"):
        bits.append(f"> *Derived:* {entry['derived']}")
    if entry.get("residue"):
        bits.append(f"> *Residue:* {entry['residue']}")
    return "\n>\n".join(bits)


_TABLE_RULE = re.compile(r"^\|(?:-+\|)+$")


def _filled_rows(body: str) -> int:
    """Data rows in ``body``'s tables — header and rule lines excluded.

    The measure behind the cover's "table rows filled from this bundle". It is
    deliberately crude and deliberately honest: it counts what a reader would
    count. A section whose tables come back at zero is a shape waiting for a
    person, and saying how many of those there are is the difference between a
    coverage block and a boast.
    """
    lines = [ln for ln in body.splitlines() if ln.startswith("|")]
    rules = sum(1 for ln in lines if _TABLE_RULE.match(ln))
    # every table contributes one header line and one rule line
    return max(0, len(lines) - 2 * rules)


def render(facts: FolderFacts, spec: dict, meta: dict) -> str:
    by_anchor = {s["anchor"]: s for s in spec["sections"]}
    sections = load_outline_sections()
    for section in sections:
        if section["anchor"] not in by_anchor:
            raise SystemExit(
                f"section-spec.yaml has no entry for outline anchor {section['anchor']!r} — "
                "the spec test should have caught this; run "
                "tests/unit/test_sdlc_runbook_generator.py"
            )

    # Render the BODY sections first, so the cover's coverage block can report
    # what this run actually produced rather than what the spec hopes for. The
    # front matter is emitted last and placed first.
    bodies: dict[str, str] = {}
    for section in sections:
        anchor = section["anchor"]
        if anchor == "front-matter":
            continue
        bodies[anchor] = RENDERERS[by_anchor[anchor]["fill"]](by_anchor[anchor], facts, meta)

    filled = sum(_filled_rows(body) for body in bodies.values())
    empty_tables = sum(
        1
        for anchor, body in bodies.items()
        if "|---" in body and _filled_rows(body) == 0 and not by_anchor[anchor].get("na_for_batch")
    )
    meta = {
        **meta,
        "counts": _counts(spec),
        "filled_rows": filled,
        "empty_table_sections": empty_tables,
    }

    out: list[str] = []
    for section in sections:
        anchor = section["anchor"]
        entry = by_anchor[anchor]
        out.append(f"<!-- anchor: {anchor} -->")
        if anchor == "front-matter":
            out.append(RENDERERS[entry["fill"]](entry, facts, meta))
        else:
            hashes = "#" * section["level"]
            out.append(f"{hashes} {section['number']} {section['heading']}")
            out.append("")
            out.append(_marker(entry))
            out.append("")
            out.append(bodies[anchor])
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def _coverage_report(facts: FolderFacts, spec: dict) -> str:
    counts = _counts(spec)
    lines = [
        f"folder      : {facts.folder_name}",
        f"provenance  : {facts.provenance}",
        f"venue       : {facts.venue}",
        f"jobs        : {len(facts.jobs)}",
        f"artifacts   : {len(facts.commands())} ({len(facts.shell_scripts())} shell script(s))",
        f"conditions  : {len(facts.conditions_in)} in / {len(facts.conditions_out)} out",
        f"contacts    : {len(facts.contacts)}",
        f"attribution : {facts.app_id_origin}",
        "sections    : "
        + ", ".join(
            f"{k}={counts[k]}" for k in ("total", "graph", "graph-partial", "manual", "na")
        ),
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Generate an SDLC Application Run Book for one Control-M folder."
    )
    ap.add_argument("--folder", required=True, help="the Control-M folder (sched_table) name")
    ap.add_argument(
        "--source",
        choices=("samples", "graph"),
        default="samples",
        help="samples = the bundled CSVs (works in any clone); graph = the DryDocs graph",
    )
    ap.add_argument("--database", default=None, help="graph source only: the Neo4j database")
    ap.add_argument("--out", type=Path, default=None, help="write here instead of stdout")
    ap.add_argument("--project", default="", help="project name for the cover")
    ap.add_argument("--version", default="0.1-generated", help="document version for the cover")
    ap.add_argument(
        "--classification",
        choices=("External", "Internal-Public", "Internal"),
        default="Internal",
        help="DryDocs classification for the cover; a FILLED run book is Internal",
    )
    ap.add_argument("--reflects", default="", help="the commit or extract this revision reflects")
    ap.add_argument(
        "--coverage-only",
        action="store_true",
        help="print what the bundle holds and exit, without rendering a document",
    )
    args = ap.parse_args(argv)

    if args.source == "samples":
        facts = load_from_samples(args.folder)
    else:
        # Function-local on purpose: the samples path must not pay for the CLI.
        from drydocs.cli import _client

        database = args.database or "the configured database"
        with _client(args.database) as client:
            facts = load_from_graph(client, args.folder, venue=f"graph database {database}")

    spec = load_spec()
    if args.coverage_only:
        print(_coverage_report(facts, spec))
        return 0

    document = render(
        facts,
        spec,
        {
            "project": args.project,
            "version": args.version,
            "reflects": args.reflects,
            "classification": args.classification,
        },
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        # newline="\n" explicitly: on Windows the default translates every \n to
        # \r\n, so the same bundle would render different BYTES on two machines
        # and any determinism check would be comparing platforms, not output.
        # Nothing guards this directory for it — test_render_determinism's
        # newline sweep does not reach `.claude/**` — so it is written here.
        args.out.write_text(document, encoding="utf-8", newline="\n")
        print(f"wrote {args.out}")
        print(_coverage_report(facts, spec))
    else:
        print(document)
    return 0


if __name__ == "__main__":
    sys.exit(main())
