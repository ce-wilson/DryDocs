"""Deterministic synthetic stand-ins for the registered sources, themed on the
Neo4j Matrix sample graph.

Every generated table is a pure function of ``(config/source-descriptors.yaml,
seed)``: a seeded ``random.Random`` decides the few choices that are choices,
everything else is arithmetic over fixed name lists, and every row carries the
``record_origin`` column set to ``sample`` so a fixture can never pass for a
capture. Names are borrowed from a film; no value here describes anything
real (SEAL ids stay inside ``RESERVED_SEALID_RANGE``, addresses end in
``example.invalid``, hosts and data centers are fictional).

The generator writes CSV TEXT, not files — packing into the gzip bundle and
extracting into landing zones is ``bundle.py``'s job, so the same bytes reach
the repo bundle and the loader's drop directory.
"""

from __future__ import annotations

import csv
import io
import random
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from drydocs.seal_samples import RESERVED_SEALID_RANGE, SYNTHETIC_EMAIL_DOMAIN
from drydocs_core.source_descriptors import SourceDescriptors

CAPTURE_TS = "2026-04-29 03:00:00"
CAPTURE_STAMP = "20260429030000"

# -- the theme ------------------------------------------------------------------
# Crew names double as people; ships as product lines; programs as products and
# applications. Nothing below is a real person, team, system or host.
PEOPLE: tuple[tuple[str, str], ...] = (
    ("Thomas", "Anderson"),
    ("Trinity", "Zion"),
    ("Morpheus", "Nebuchadnezzar"),
    ("Cypher", "Reagan"),
    ("Tank", "Operator"),
    ("Dozer", "Operator"),
    ("Apoc", "Crew"),
    ("Switch", "Crew"),
    ("Mouse", "Programmer"),
    ("Niobe", "Logos"),
    ("Ghost", "Logos"),
    ("Link", "Operator"),
    ("Zee", "Dockworker"),
    ("Kid", "Council"),
    ("Seraph", "Guardian"),
    ("Sati", "Program"),
    ("Roland", "Mjolnir"),
    ("Ballard", "Caduceus"),
    ("Mifune", "Defense"),
    ("Lock", "Commander"),
    ("Bane", "Caduceus"),
    ("Sparks", "Logos"),
    ("Persephone", "Club"),
    ("Keymaker", "Program"),
)
LOBS: tuple[tuple[str, str, str], ...] = (
    ("LOB701", "ZION", "Zion Council"),
    ("LOB702", "MTX", "Matrix Operations"),
    ("LOB703", "MCH", "Machine City"),
)
SHIPS: tuple[tuple[str, str], ...] = (
    ("NEB", "Nebuchadnezzar"),
    ("LOG", "Logos"),
    ("VIG", "Vigilant"),
    ("MJO", "Mjolnir"),
    ("ICA", "Icarus"),
    ("OSI", "Osiris"),
)
PROGRAMS: tuple[str, ...] = (
    "Construct",
    "Loading Program",
    "Jump Program",
    "Agent Training",
    "Sentinel Tracker",
    "Oracle Kitchen",
    "Keymaker Vault",
    "Trainman Station",
    "Merovingian Ledger",
    "Zion Dock Control",
    "Pirate Broadcast",
    "Red Pill Dispenser",
    "Deja Vu Detector",
    "Operator Console",
    "Broadcast Depth Gauge",
    "Hovercraft Telemetry",
)
ROLE_IDS: tuple[str, ...] = (
    "tech_partner",
    "principal_engineer",
    "area_tech_partner",
    "head_of_technology",
)
CONTACT_ROLES: tuple[str, ...] = ("Business Owner", "Design Authority")
CI_CLASSES: tuple[tuple[str, str, str], ...] = (
    ("cmdb_ci", "", "Configuration Item"),
    ("cmdb_ci_server", "cmdb_ci", "Server"),
    ("cmdb_ci_linux_server", "cmdb_ci_server", "Linux Server"),
    ("cmdb_ci_db_instance", "cmdb_ci", "Database Instance"),
    ("cmdb_ci_appl", "cmdb_ci", "Application"),
    ("cmdb_ci_business_app", "cmdb_ci", "Business Application"),
    ("cmdb_ci_service", "cmdb_ci", "Service"),
    ("cmdb_ci_scheduler", "cmdb_ci_appl", "Job Scheduler"),
    ("cmdb_ci_storage_volume", "cmdb_ci", "Storage Volume"),
    ("cmdb_ci_network_gear", "cmdb_ci", "Network Gear"),
)


@dataclass(frozen=True)
class Table:
    """One generated CSV: the SOURCE-mode file name, its header and rows."""

    source_id: str
    name: str
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]

    def to_csv(self) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(self.header)
        writer.writerows(self.rows)
        return buf.getvalue()


def _sid(n: int) -> str:
    """A synthetic SID: letter + six digits, in a block no directory issues."""
    return f"K{700000 + n:06d}"


def _person(n: int) -> tuple[str, str, str]:
    first, last = PEOPLE[n % len(PEOPLE)]
    return _sid(n), f"{first} {last}", f"{first}.{last}@{SYNTHETIC_EMAIL_DOMAIN}".lower()


class SyntheticSources:
    """Generate every planned table. Construct once; ``tables()`` is pure."""

    def __init__(self, descriptors: SourceDescriptors) -> None:
        self.descriptors = descriptors
        cfg = descriptors.synthetic
        self.seed = int(cfg.get("seed", 0))
        self.origin_field = cfg.get("record_origin_field", "record_origin")
        self.origin_value = cfg.get("record_origin_value", "sample")
        self.rows: Mapping[str, int] = dict(cfg.get("rows") or {})
        self._wanted: dict[str, tuple[str, ...]] = {
            plan.source_id: plan.files for plan in descriptors.synthetic_plans()
        }

    # ------------------------------------------------------------ helpers
    def _n(self, key: str, default: int) -> int:
        return int(self.rows.get(key, default))

    def _table(
        self, source_id: str, name: str, header: Iterable[str], rows: Iterable[Iterable[str]]
    ) -> Table:
        hdr = (*header, self.origin_field)
        return Table(
            source_id,
            name,
            hdr,
            tuple((*map(str, r), self.origin_value) for r in rows),
        )

    def _apps(self) -> list[tuple[int, str, str]]:
        """(seal_id, name, lob_code) for every synthetic application."""
        count = min(self._n("applications", 12), len(PROGRAMS), len(RESERVED_SEALID_RANGE))
        return [
            (RESERVED_SEALID_RANGE[i], PROGRAMS[i], LOBS[i % len(LOBS)][1]) for i in range(count)
        ]

    # ------------------------------------------------------------- tables
    def tables(self) -> tuple[Table, ...]:
        rng = random.Random(self.seed)
        built = {t.name: t for t in self._build(rng)}
        out: list[Table] = []
        for source_id, files in sorted(self._wanted.items()):
            for name in files:
                if name not in built:
                    raise KeyError(f"{source_id}: no generator for planned file {name!r}")
                t = built[name]
                out.append(Table(source_id, t.name, t.header, t.rows))
        return tuple(out)

    def _build(self, rng: random.Random) -> list[Table]:  # - one table per block
        apps = self._apps()
        tables: list[Table] = []

        # -- product catalog ------------------------------------------------
        tables.append(
            self._table(
                "pat:product-catalog",
                "catalog_lobs.csv",
                ("lob_id", "code", "name", "reconciles_to_segment", "reconcile_confidence"),
                [(lob_id, code, name, code, "1.0") for lob_id, code, name in LOBS],
            )
        )
        lines = [
            (f"PL_{code}", ship, LOBS[i % len(LOBS)][0]) for i, (code, ship) in enumerate(SHIPS)
        ]
        tables.append(
            self._table(
                "pat:product-catalog",
                "product_lines.csv",
                ("product_line_id", "name", "parent_lob_id"),
                lines,
            )
        )
        products = [
            (f"PROD_{lines[i % len(lines)][0][3:]}_{i + 1:02d}", name, lines[i % len(lines)][0])
            for i, (_, name, _) in enumerate(apps)
        ]
        tables.append(
            self._table(
                "pat:product-catalog",
                "products.csv",
                ("product_id", "name", "parent_product_line_id"),
                products,
            )
        )

        # -- teams and people ---------------------------------------------
        team_count = self._n("teams", 6)
        teams = [
            (
                f"T{7001 + i}",
                f"{SHIPS[i % len(SHIPS)][1]} Crew",
                f"JIRA-{SHIPS[i % len(SHIPS)][0]}",
                products[i % len(products)][0],
            )
            for i in range(team_count)
        ]
        tables.append(
            self._table(
                "pat:people-report",
                "dev_teams.csv",
                ("team_id", "name", "jira_board_id", "parent_product_id"),
                teams,
            )
        )
        roles_per = self._n("roles_per_team", 2)
        role_rows = []
        person = 0
        for team_id, *_ in teams:
            for r in range(roles_per):
                sid, _, _ = _person(person)
                role_rows.append(
                    (team_id, sid, ROLE_IDS[(person + r) % len(ROLE_IDS)], "2026-01-01", "")
                )
                person += 1
        tables.append(
            self._table(
                "pat:people-report",
                "pat_team_roles.csv",
                ("team_id", "employee_sid", "role_id", "valid_from", "valid_to"),
                role_rows,
            )
        )
        mapping_rows = []
        for i, (team_id, _, _, product_id) in enumerate(teams):
            owned = [str(a[0]) for a in apps[i::team_count]]
            team_type = rng.choice(("dedicated", "aligned", "flex"))
            mapping_rows.append(
                (
                    team_id,
                    product_id,
                    f"AP_{SHIPS[i % len(SHIPS)][0]}",
                    "; ".join(owned),
                    team_type,
                    "false",
                    "",
                    "",
                )
            )
        tables.append(
            self._table(
                "pat:product-catalog",
                "pat_product_mapping.csv",
                (
                    "team_id",
                    "product_id",
                    "area_product_id",
                    "seal_ids",
                    "team_type",
                    "sponsored",
                    "sponsored_product_id",
                    "sponsored_area_product_id",
                ),
                mapping_rows,
            )
        )

        # -- applications and contacts -------------------------------------
        app_rows = []
        contact_rows = []
        contacts_per = self._n("contacts_per_application", 2)
        for i, (seal_id, name, lob) in enumerate(apps):
            owner = _person(i)
            cto = _person(i + 7)
            info = _person(i + 13)
            short = "".join(w[0] for w in name.split()).upper()
            app_rows.append(
                (
                    str(seal_id),
                    name,
                    short,
                    "Active",
                    lob,
                    "Internal",
                    owner[0],
                    owner[1],
                    cto[0],
                    cto[1],
                    info[0],
                    info[1],
                )
            )
            for c in range(contacts_per):
                sid, full, email = _person(i * contacts_per + c + 3)
                contact_rows.append(
                    (str(seal_id), CONTACT_ROLES[c % len(CONTACT_ROLES)], sid, full, email)
                )
        tables.append(
            self._table(
                "seal:app-extract",
                "seal_applications.csv",
                (
                    "app_id",
                    "name",
                    "app_short_name",
                    "app_state",
                    "app_lob",
                    "info_classification",
                    "app_owner_sid",
                    "app_owner_name",
                    "chief_tech_officer_sid",
                    "chief_tech_officer_name",
                    "info_owner_sid",
                    "info_owner_name",
                ),
                app_rows,
            )
        )
        tables.append(
            self._table(
                "seal:app-extract",
                "seal_contacts.csv",
                ("app_id", "role_name", "employee_sid", "employee_name", "employee_email"),
                contact_rows,
            )
        )

        # -- servers ----------------------------------------------------------
        servers_per = self._n("servers_per_application", 2)
        server_rows = []
        for i, (seal_id, name, _) in enumerate(apps):
            slug = name.split()[0].lower()
            for s in range(servers_per):
                designation = "PROD" if s == 0 else "DR"
                dc = "ZION-DC1" if s == 0 else "MACH-DC1"
                server_rows.append(
                    (
                        f"zion-{slug}-{s + 1:02d}",
                        "RHEL",
                        "9.4",
                        f"R{(i % 8) + 1:02d}",
                        dc,
                        "Zion" if s == 0 else "Machine City",
                        "ZN",
                        "ZZ",
                        designation,
                        str(seal_id),
                    )
                )
        tables.append(
            self._table(
                "infra:server-export",
                "server_inventory.csv",
                (
                    "server_name",
                    "os_product",
                    "os_version",
                    "rack",
                    "data_center",
                    "city",
                    "state",
                    "country",
                    "designation",
                    "business_application",
                ),
                server_rows,
            )
        )

        # -- CMDB CI classes --------------------------------------------------
        tables.append(
            self._table(
                "snow:cmdb-ci-classes",
                "cmdb_ci_classes.csv",
                ("ci_class", "parent_class", "label"),
                CI_CLASSES[: self._n("ci_classes", 8)],
            )
        )

        # -- Control-M: folders, jobs, conditions, dependencies, hosts ---------
        folder_count = self._n("folders", 4)
        jobs_per = self._n("jobs_per_folder", 5)
        folders = []
        for f in range(folder_count):
            seal_id, name, _ = apps[f % len(apps)]
            ship = SHIPS[f % len(SHIPS)][0]
            token = name.split()[0].upper()[:4]
            folders.append(
                (
                    761001 + f,
                    f"PZN{ship[:3]}G-{ship}-{seal_id}-{token}-DLY",
                    ship,
                    token,
                    seal_id,
                )
            )
        tables.append(
            self._table(
                "controlm@[db].psgmgr.cm_def_vtab",
                "controlm_folders.csv",
                (
                    "folder_id",
                    "sched_table",
                    "data_center",
                    "user_daily",
                    "table_status",
                    "table_type",
                    "instance_name",
                    "last_updated",
                    "last_updated_user",
                    "capture_date",
                ),
                [
                    (
                        fid,
                        sched,
                        "Z01",
                        "Y",
                        "A",
                        "2",
                        "ZION-EAST",
                        CAPTURE_TS,
                        "svc.operator",
                        CAPTURE_TS,
                    )
                    for fid, sched, *_ in folders
                ],
            )
        )
        job_rows = []
        jobs: list[tuple[int, int, str]] = []  # (folder_id, job_id, job_name)
        job_id = 0
        for fid, sched, ship, token, _ in folders:
            for j in range(jobs_per):
                job_id += 1
                job_name = f"PZN{ship[0]}D{job_id:04d}_{ship}_{token}_STEP{j + 1}"
                author = PEOPLE[(job_id + 3) % len(PEOPLE)][0].lower()
                jobs.append((fid, job_id, job_name))
                job_rows.append(
                    (
                        str(job_id),
                        "1",
                        str(fid),
                        job_name,
                        sched,
                        ship,
                        token,
                        "Job",
                        "N",
                        "",
                        str(j + 1),
                        f"svc.{ship.lower()}",
                        author,
                        f"host-{ship.lower()}-{(j % 2) + 1:02d}",
                        f"/opt/zion/{ship.lower()}/{token.lower()}_step{j + 1}.sh",
                        f"{token.title()} step {j + 1} of {jobs_per}",
                        "",
                        "5",
                        "Y" if j == jobs_per - 1 else "N",
                        "",
                        "",
                        "Y" if j == jobs_per - 1 else "N",
                        "Y",
                        "U",
                        CAPTURE_STAMP,
                        author,
                        "ZION-EAST",
                        CAPTURE_TS,
                    )
                )
        tables.append(
            self._table(
                "controlm@[db].psgmgr.cm_def_vjob",
                "controlm_jobs.csv",
                (
                    "job_id",
                    "version_serial",
                    "folder_id",
                    "job_name",
                    "parent_table",
                    "application",
                    "group_name",
                    "task_type",
                    "cyclic",
                    "cyclic_type",
                    "job_order",
                    "owner",
                    "author",
                    "node_id",
                    "cmd_line",
                    "description",
                    "memname",
                    "priority",
                    "critical",
                    "active_from",
                    "active_till",
                    "end_folder",
                    "is_current_version",
                    "version_opcode",
                    "version_timestamp",
                    "version_user",
                    "instance_name",
                    "capture_date",
                ),
                job_rows,
            )
        )
        # Conditions: each job posts <job>-OK; the next job in the same folder waits
        # on it; the first job of folder k+1 also waits on the last job of folder k.
        cond_in, cond_out, deps = [], [], []
        for idx, (fid, jid, jname) in enumerate(jobs):
            cond_out.append(
                (str(fid), str(jid), "1", f"{jname}-OK", "ODAT", "+", "1", "U", "Y", CAPTURE_TS)
            )
            if idx > 0:
                pfid, pjid, pname = jobs[idx - 1]
                cond_in.append(
                    (
                        str(fid),
                        str(jid),
                        "1",
                        f"{pname}-OK",
                        "ODAT",
                        "AND",
                        "",
                        "1",
                        "1",
                        "U",
                        "Y",
                        CAPTURE_TS,
                    )
                )
                deps.append((f"{fid}.{jid}", f"{pname}-OK", f"{pfid}.{pjid}"))
        tables.append(
            self._table(
                "controlm@[db].psgmgr.cm_def_lnki_p_vw",
                "controlm_conditions_in.csv",
                (
                    "folder_id",
                    "job_id",
                    "version_serial",
                    "condition_name",
                    "odate",
                    "and_or",
                    "parentheses",
                    "order_",
                    "isn",
                    "version_opcode",
                    "is_current_version",
                    "capture_date",
                ),
                cond_in,
            )
        )
        tables.append(
            self._table(
                "controlm@[db].psgmgr.cm_def_lnko_p_vw",
                "controlm_conditions_out.csv",
                (
                    "folder_id",
                    "job_id",
                    "version_serial",
                    "condition_name",
                    "odate",
                    "sign",
                    "isn",
                    "version_opcode",
                    "is_current_version",
                    "capture_date",
                ),
                cond_out,
            )
        )
        tables.append(
            self._table(
                "controlm@[db].psgmgr.cm_def_lnki_p_vw",
                "controlm_dependencies.csv",
                ("in_table_job_id", "out_condition", "out_table_job_id"),
                deps,
            )
        )
        host_count = self._n("hosts", 6)
        host_rows = [
            (
                "Z01-E0700-ZIO",
                f"host-{SHIPS[h % len(SHIPS)][0].lower()}-01",
                f"host-{SHIPS[h % len(SHIPS)][0].lower()}-{(h % 2) + 1:02d}",
                "P",
                CAPTURE_TS,
            )
            for h in range(host_count)
        ]
        tables.append(
            self._table(
                "controlm@[db].psgmgr.cm_hosts",
                "controlm_hosts.csv",
                ("data_center", "grpname", "nodeid", "participation_type", "capture_date"),
                host_rows,
            )
        )
        return tables
