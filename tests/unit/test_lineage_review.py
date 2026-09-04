"""Lineage SME review page — port of depgraph's test_html_review.py (0002-C §4).

Same expectations as the prototype's suite (self-contained page, folder sections,
job metadata, dependency kinds, assertion panel, per-folder notes + export),
adapted to the re-homed surface: LineageGraph, node_target instead of host, the
registered rel spellings.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from drydocs_lineage.extractors import ControlMInventoryExtractor
from drydocs_lineage.model import (
    DataAssetNode,
    LineageGraph,
    ProcessNode,
    asset_id,
    process_id,
)
from drydocs_lineage.review import to_html

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "lineage" / "jobs.csv"


@pytest.fixture()
def page() -> str:
    g = LineageGraph()
    ControlMInventoryExtractor().extract(FIXTURE, g)
    return to_html(g, doc_id="synthetic-twin", generated_at="2026-07-11 00:00 UTC")


def test_self_contained(page: str) -> None:
    # no external resources — everything inline (a strict-CSP SME browser must render it)
    assert page.startswith("<!doctype html>")
    assert "<style>" in page and "<script>" in page
    assert "http://" not in page
    assert "src=" not in page


def test_shows_folder_sections_and_jobs(page: str) -> None:
    assert "PRARAG-HLDM-70011-PEX-TRUST-DLY" in page
    assert "PEX_SPARK_REFINE" in page


def test_shows_run_as_and_node_target(page: str) -> None:
    assert "svc.hldm" in page
    assert "host-emr-01" in page
    # the polymorphic wording, not the prototype's "host (server)" claim
    assert "node target" in page


def test_shows_invoked_dependency_kinds(page: str) -> None:
    assert "pyspark" in page
    assert "abinitio" in page
    assert "INVOKES" in page


def test_assertion_panel_passes_for_clean_fixture(page: str) -> None:
    # fixture jobs all carry node_target + run_as and every cmd_line resolves
    assert "all checks passed" in page


def test_comment_box_per_folder_and_export(page: str) -> None:
    assert 'class="note"' in page
    assert "exportNotes()" in page
    assert "drydocs-lineage-review-" in page  # localStorage namespace is ours


def test_every_dependency_row_carries_a_decision_control_keyed_by_its_rel(page: str) -> None:
    """LIN2 (b): the per-rel decision. Each dep row's control names the rel triple the
    graph carries (from / type / to are the node ids and the registered label), so an
    exported decision joins to a candidate by equality. The export writes the
    drydocs.lineage-decisions.v1 shape the load reads."""
    g = LineageGraph()
    ControlMInventoryExtractor().extract(FIXTURE, g)
    controls = re.findall(
        r'<select class="decide" data-from="([^"]*)" data-type="([^"]*)" data-to="([^"]*)"', page
    )
    assert controls, "a decision control per dependency row"
    from html import unescape

    rendered = {(unescape(a), unescape(b), unescape(c)) for a, b, c in controls}
    assert rendered <= g.rels and len(rendered) == len(controls)
    assert "drydocs.lineage-decisions.v1" in page
    assert "decision:s.value" in page and "drydocs-lineage-decisions-" in page
    assert "Export decisions + notes" in page


def test_html_escaped() -> None:
    # markup-looking tokens in a cmd_line must be escaped, never raw
    g = LineageGraph()
    g.add_process(
        ProcessNode(
            node_id=process_id("controlm_job", "1.2"),
            kind="controlm_job",
            name="J_ESC",
            command="run.sh --tag <odate> & echo 'x'",
            node_target="host-x",
            run_as="svc.x",
            folder="F",
        )
    )
    html = to_html(g, doc_id="esc")
    assert "<odate>" not in html
    assert "&lt;odate&gt;" in html


def test_unresolved_dependency_flags_review_needed() -> None:
    # an INVOKES child of kind "unknown" (unclassified cmd_line) must flip the panel
    g = LineageGraph()
    jid = process_id("controlm_job", "1.2")
    cid = process_id("unknown", "mystery_bin")
    g.add_process(
        ProcessNode(
            node_id=jid, kind="controlm_job", name="J", node_target="h", run_as="u", folder="F"
        )
    )
    g.add_process(ProcessNode(node_id=cid, kind="unknown", name="mystery_bin"))
    g.add_rel(jid, "INVOKES", cid)
    html = to_html(g, doc_id="warn")
    assert "review needed" in html
    assert "1 unresolved" in html


def test_unresolved_file_op_candidate_flags_review_needed() -> None:
    """G14: the writer's would-be drop (WritePlan.unresolved_file_ops) must not
    sit unread — a script-src file-op candidate with no owning job flips the
    assertion panel BEFORE any plan is cut."""
    g = LineageGraph()
    sid = process_id("shell_script", "/opt/orphan.ksh")
    aid = asset_id("local_file", "/data/x.dat")
    g.add_process(
        ProcessNode(node_id=sid, kind="shell_script", name="orphan.ksh", path="/opt/orphan.ksh")
    )
    g.add_data_asset(DataAssetNode(node_id=aid, kind="local_file", location="/data/x.dat"))
    g.add_rel(sid, "READS_FROM", aid)  # no job INVOKES sid anywhere
    html = to_html(g, doc_id="fops")
    assert "review needed" in html
    assert "unresolved_file_ops" in html


def test_file_op_candidates_render_on_the_job_card() -> None:
    """A job-src file-op candidate (the G14 extractor feed) renders on the job
    card with the registered spelling and the asset location; the assertion
    panel stays green (a job src IS its own Activity)."""
    g = LineageGraph()
    jid = process_id("controlm_job", "161015.22")
    aid = asset_id("local_file", "/data/arch/loans.dat.gz")
    g.add_process(
        ProcessNode(
            node_id=jid,
            kind="controlm_job",
            name="JOB_ARCHIVE",
            node_target="h",
            run_as="svc.x",
            folder="F",
            command="gzip /data/arch/loans.dat",
        )
    )
    g.add_data_asset(
        DataAssetNode(
            node_id=aid,
            kind="local_file",
            location="/data/arch/loans.dat.gz",
        )
    )
    g.add_rel(jid, "WRITES_TO", aid)
    html = to_html(g, doc_id="fop-card")
    assert "all checks passed" in html
    assert "WRITES_TO" in html
    assert "local_file" in html
    assert "/data/arch/loans.dat.gz" in html


def test_prototype_rel_spellings_render_as_registered(page_graph=None) -> None:
    # READS normalizes to READS_FROM at the model layer; the page shows the
    # registered spelling only
    g = LineageGraph()
    jid = process_id("controlm_job", "1.2")
    cid = process_id("shell_script", "/opt/x.sh")
    g.add_process(
        ProcessNode(
            node_id=jid, kind="controlm_job", name="J", node_target="h", run_as="u", folder="F"
        )
    )
    g.add_process(ProcessNode(node_id=cid, kind="shell_script", name="x.sh"))
    g.add_rel(jid, "READS", cid)  # prototype spelling in, registered out
    html = to_html(g, doc_id="rels")
    assert "READS_FROM" in html


def test_empty_graph_page_points_at_the_cli() -> None:
    html = to_html(LineageGraph(), doc_id="empty")
    assert "No Control-M jobs in this graph" in html
    assert "lineage-review" in html
