"""The supplement chain (G29) — registry, order, verification, run log.

Before G29 each ``*_supplement.cypher`` had its own hand-written CLI verb whose
body was the same four lines, and the ORDER of the chain lived only in prose.
Two things were unguarded and are guarded here:

* **Order.** ``catalog`` reuses the ``:Attribution`` class and ``#hasAgent``
  term that ``seal`` declares, so seal MUST precede catalog. Prose said so in
  four places (repo-README, runbook, the .cypher headers, the skill) — and the
  ``run-drydocs`` skill listed them the wrong way round anyway.
* **Landing.** ``execute_file`` raises on a Cypher error, but a supplement that
  is truncated, renamed, or comment-only runs "fine" and seeds nothing. That
  surfaces much later as a loader MATCH that silently matches zero canonical
  :Role nodes. The chain now asserts every declared :OntologyTerm IRI is
  present after the apply.

No Neo4j: the chain runner is driven against a fake client that models the
graph as a set of IRIs.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from drydocs import cli as cli_mod
from drydocs_core.schema import supplements as sup

runner = CliRunner()


# ---- the registry -----------------------------------------------------------


def test_registry_order_is_the_documented_chain() -> None:
    assert [s.name for s in sup.SUPPLEMENTS] == [
        "base",
        "seal",
        "catalog",
        "registry",
        "sosa",
    ]
    # The reason the order exists — catalog reuses seal's Attribution/#hasAgent.
    names = [s.name for s in sup.SUPPLEMENTS]
    assert names.index("seal") < names.index("catalog")
    assert names.index("base") == 0


def test_sosa_is_opt_in_and_never_in_the_default_chain() -> None:
    assert sup.BY_NAME["sosa"].opt_in is True
    assert [s.name for s in sup.default_chain()] == ["base", "seal", "catalog", "registry"]
    assert all(not s.opt_in for s in sup.default_chain())


def test_every_supplement_file_exists_and_declares_terms() -> None:
    for s in sup.SUPPLEMENTS:
        assert s.path.exists(), f"{s.name}: {s.path} missing"
        assert sup.declared_terms(s.path), f"{s.name} declares no OntologyTerm IRIs"


def test_no_supplement_file_on_disk_is_silently_outside_the_chain() -> None:
    """G59: a ``*supplement*.cypher`` beside the registry that the chain omits
    must fail BY NAME — a locally added supplement (the consumer's
    quantitative-resource-pools case) cannot be quietly skipped by
    ``apply-supplements``. A deliberate omission goes in CHAIN_EXCLUSIONS with
    a written reason."""
    missing = sup.unchained_supplement_files()
    assert not missing, (
        f"supplement file(s) on disk but absent from the ordered chain: {list(missing)} "
        "— add each to SUPPLEMENTS (order is load-bearing — see the module docstring) "
        "or to CHAIN_EXCLUSIONS with a written reason"
    )


def test_unchained_detection_names_the_dropped_file(tmp_path, monkeypatch) -> None:
    """The guard actually fires: a supplement-shaped file appearing beside the
    module is reported by NAME, not swallowed into a count."""
    for s in sup.SUPPLEMENTS:
        (tmp_path / s.filename).write_text("// copy", encoding="utf-8")
    (tmp_path / "quantitative_ontology_supplement.cypher").write_text("// new", encoding="utf-8")
    monkeypatch.setattr(sup, "SCHEMA_DIR", tmp_path)
    assert sup.unchained_supplement_files() == ("quantitative_ontology_supplement.cypher",)


def test_chain_exclusions_are_real_reasoned_and_not_contradictory() -> None:
    """Exclusion hygiene (the SCHEDULED_INGEST_EXCLUSIONS idiom): every entry
    names a file that exists (else the exclusion is stale), that is NOT also in
    the chain (else it is contradictory), and carries a written reason — a bare
    token reads as cargo cult."""
    chained = {s.filename for s in sup.SUPPLEMENTS}
    for filename, reason in sup.CHAIN_EXCLUSIONS.items():
        assert (sup.SCHEMA_DIR / filename).exists(), f"stale exclusion: {filename} not on disk"
        assert filename not in chained, f"{filename} is excluded AND chained — contradictory"
        assert len(reason.split()) >= 5, f"{filename}: the reason must be a sentence, not a token"


def test_declared_terms_reads_the_iris_the_file_merges() -> None:
    base = sup.declared_terms(sup.BY_NAME["base"].path)
    for anchor in ("ControlMServer", "ControlMFolder", "ControlMJob"):
        assert f"https://drydocs.local/ontology#{anchor}" in base
    # seal's Attribution class is the term catalog depends on — the order's reason.
    seal = sup.declared_terms(sup.BY_NAME["seal"].path)
    assert "https://drydocs.local/ontology#Attribution" in seal


def test_declared_terms_ignores_comments_and_non_merge_mentions(tmp_path) -> None:
    """Only a live MERGE counts — a MATCH or a retired (commented) MERGE must not.

    Commenting out a term is how a term is retired; if the parser still saw it,
    the chain would demand a term the file no longer creates and fail forever.
    """
    f = tmp_path / "probe.cypher"
    f.write_text(
        '// MERGE (n:OntologyTerm {iri: "https://example.org/line-commented"})\n'
        '/* MERGE (n:OntologyTerm {iri: "https://example.org/block-commented"}) */\n'
        'MATCH (n:OntologyTerm {iri: "https://example.org/matched"}) RETURN n;\n'
        'MERGE (n:OntologyTerm:LocalClass {iri: "https://example.org/real"}) SET n.label = "x";\n',
        encoding="utf-8",
    )
    assert sup.declared_terms(f) == frozenset({"https://example.org/real"})


def test_declared_terms_keeps_slashes_inside_the_iri(tmp_path) -> None:
    """`//` in a quoted IRI is data, not a comment — the whole point of the
    shared comment/string-aware scanner."""
    f = tmp_path / "probe.cypher"
    f.write_text(
        'MERGE (n:OntologyTerm:ProvClass {iri: "http://www.w3.org/ns/prov#Entity"});\n',
        encoding="utf-8",
    )
    assert sup.declared_terms(f) == frozenset({"http://www.w3.org/ns/prov#Entity"})


# ---- the CLI surface ---------------------------------------------------------


def _command_names() -> set[str]:
    return {c.name for c in cli_mod.app.registered_commands}


def test_new_verb_and_every_legacy_verb_are_registered() -> None:
    names = _command_names()
    assert "apply-supplements" in names
    for s in sup.SUPPLEMENTS:
        assert s.legacy_verb in names, f"legacy verb {s.legacy_verb} disappeared"


def test_legacy_verb_names_are_the_ones_the_docs_publish() -> None:
    assert {s.legacy_verb for s in sup.SUPPLEMENTS} == {
        "apply-ontology-supplement",
        "apply-seal-supplement",
        "apply-catalog-supplement",
        "apply-registry-supplement",
        "apply-sosa-supplement",
    }


# ---- the chain runner --------------------------------------------------------


class _FakeClient:
    """Models the graph as the set of :OntologyTerm IRIs it holds."""

    def __init__(self, *, seed_from: set[str] | None = None, apply_nothing: bool = False) -> None:
        self.iris: set[str] = set(seed_from or ())
        self.applied: list[str] = []
        self._apply_nothing = apply_nothing

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def connection_info(self) -> dict[str, str]:
        return {"uri": "bolt://fake:7687", "user": "u", "database": "drydocs"}

    def execute_file(self, path) -> None:
        self.applied.append(path.name)
        if not self._apply_nothing:
            self.iris |= sup.declared_terms(path)

    def run(self, cypher: str, params: dict | None = None):
        params = params or {}
        if "count(n) AS n" in cypher:
            return [{"n": len(self.iris)}]
        if "count(DISTINCT n.iri) AS n" in cypher:
            return [{"n": len(self.iris & set(params["iris"]))}]
        return [{"iri": i} for i in self.iris & set(params.get("iris", ()))]


@pytest.fixture()
def fake_client(monkeypatch):
    holder: dict[str, _FakeClient] = {}

    def _install(client: _FakeClient) -> _FakeClient:
        holder["client"] = client
        monkeypatch.setattr(cli_mod, "_client", lambda *a, **k: client)
        return client

    return _install


def test_chain_applies_in_registry_order(fake_client, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    client = fake_client(_FakeClient())
    result = runner.invoke(cli_mod.app, ["apply-supplements"])
    assert result.exit_code == 0, result.output
    assert client.applied == [s.filename for s in sup.default_chain()]
    assert "4 supplement(s) applied and verified." in result.output


def test_chain_writes_the_run_log_envelope(fake_client, tmp_path, monkeypatch) -> None:
    logdir = tmp_path / "logs"
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(logdir))
    fake_client(_FakeClient())
    result = runner.invoke(cli_mod.app, ["apply-supplements"])
    assert result.exit_code == 0, result.output
    logs = list(logdir.glob("load.supplement.*.log"))
    assert len(logs) == 1, f"expected one load.supplement.<stamp>.log, got {logs}"
    text = logs[0].read_text(encoding="utf-8")
    assert "loader     : supplement" in text
    assert "chain      : base -> seal -> catalog -> registry" in text
    assert "target     : bolt://fake:7687 db=drydocs" in text
    assert "status               : OK" in text
    assert "terms missing        : 0" in text


def test_a_supplement_that_seeds_nothing_fails_the_command(
    fake_client, tmp_path, monkeypatch
) -> None:
    """The load-bearing check: a file that runs but lands nothing must fail."""
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    fake_client(_FakeClient(apply_nothing=True))
    result = runner.invoke(cli_mod.app, ["apply-supplements", "--only", "registry"])
    assert result.exit_code == 1, result.output
    assert "term not in graph after apply" in result.output
    log = next((tmp_path / "logs").glob("load.supplement.*.log"))
    assert "status               : FAILED" in log.read_text(encoding="utf-8")


def test_only_flag_follows_registry_order_not_flag_order(
    fake_client, tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    client = fake_client(_FakeClient())
    result = runner.invoke(
        cli_mod.app, ["apply-supplements", "--only", "catalog", "--only", "seal"]
    )
    assert result.exit_code == 0, result.output
    assert client.applied == [
        sup.BY_NAME["seal"].filename,
        sup.BY_NAME["catalog"].filename,
    ]


def test_with_sosa_appends_the_experimental_supplement(fake_client, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    client = fake_client(_FakeClient())
    result = runner.invoke(cli_mod.app, ["apply-supplements", "--with-sosa"])
    assert result.exit_code == 0, result.output
    assert client.applied[-1] == sup.BY_NAME["sosa"].filename
    assert len(client.applied) == len(sup.default_chain()) + 1


def test_unknown_only_name_exits_2_without_touching_the_graph(
    fake_client, tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    client = fake_client(_FakeClient())
    result = runner.invoke(cli_mod.app, ["apply-supplements", "--only", "nope"])
    assert result.exit_code == 2
    assert "Unknown supplement(s): nope" in result.output
    assert client.applied == []


@pytest.mark.parametrize("supplement", sup.SUPPLEMENTS, ids=lambda s: s.name)
def test_legacy_verb_delegates_to_the_same_chain(
    supplement, fake_client, tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    client = fake_client(_FakeClient())
    result = runner.invoke(cli_mod.app, [supplement.legacy_verb])
    assert result.exit_code == 0, result.output
    assert client.applied == [supplement.filename]
    # the alias inherits the envelope + verification, not just the execute
    assert list((tmp_path / "logs").glob("load.supplement.*.log"))
