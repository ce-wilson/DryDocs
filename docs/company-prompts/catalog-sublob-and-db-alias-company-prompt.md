# Company-side prompt — the `[db]` alias revert, and the Sub-LoB label

> Producer-drafted 2026-08-25 for the company-side assistant. Paste or read whole.
> Your investigation of the `[db]`/alias question and your C27 config review were both
> good work — the alias commit archaeology (`8e3bb1eb`, 2026-08-18) and the catalog gate
> reversal (`gate-log.md:1678`) are facts the producer did not have, and holding #2 rather
> than auto-applying it was the right call.
>
> **Everything here is recorded in YOUR upgrade ledger (`port-exec-state.md` / the
> PORT-REPORT) and stays there. Nothing in this prompt sends anything to the producer, and
> no reply, sha, figure or instance name is wanted back.** Guardrails stand: nothing pushes
> to the producer remote.

---

## 1. The alias: SME ruled — it is an ALIAS, not a SID, and it is still not published

The question you surfaced ("is this a deliberate divergence or drift?") is answered, and the
answer is neither of the two you offered: **it was a deliberate SME decision on 2026-08-18,
made without the port and gate implications on the table.** Your ledger should record it that
way rather than as drift — it was a considered choice, now re-ruled with the consequences
visible.

**Ruling (SME, 2026-08-25): the token is an alias name rather than a SID, and it is still not
to be published. Sanitize it.**

### Done producer-side already, landing in the next port

Three tracked publishable files were naming the alias in prose while all 28 registry ids were
carefully redacting it — the J15 lesson one level over. All three are sanitized with no loss
of meaning:

| File | Now reads |
|---|---|
| `.claude/skills/reconcile-port/SKILL.md` | "a bare TNS alias resolves only via tnsnames and won't work thin" — names none |
| `PORT-MANIFEST.yaml` | "carries the **psgmgr** §7f audit chain" |
| `docs/port/port-prompt-archive-steps-1-42.md` | same phrase, same fix |

**`psgmgr` is the correct replacement and is safe by the signed ruling itself** —
`gate-log.md:2971`: *"the DATABASE redacted to `[db]` and the schema kept."* The schema name
is published on purpose; only the database is redacted. Expect `psgmgr` to appear where the
alias used to, and do not "re-sanitize" it.

### What is yours to do

1. **Revert the 10-id substitution back to `[db]`**, with the same propagation `8e3bb1eb`
   carried: loader `source_id` ClassVars, the CLI source gate, audit-fields,
   `loader-source-overlay`, the taxonomy-ontology-map controlm mappings, unit tests, and the
   regenerated `enforcement-matrix.json`.
2. **Un-pin the alias in `test_source_registry.py`** (lines 340, 426-428, 459, 476-477, 499,
   538). Those pins fail the moment the canonical-producer file arrives regardless of this
   ruling — see §2.
3. **Delete the duplicate escalation row 549.** Do NOT rename it to `[db]`: that collides with
   615 and fails `test_shipped_registry_ids_are_unique`. **615 is the canonical row** — it
   matches producer line 559 exactly and carries the N9 grammar notes and the
   origin-under-review block. 549 is the drifted duplicate.
4. **Do not put the real name back anywhere tracked.** The producer keeps its
   placeholder→value key in `internal/`, outside the publish boundary; that file does not
   cross. Yours belongs somewhere equivalent on your side, or in
   `config/dev-environment.yaml`, which is `canonical-company` precisely so local facts never
   travel.

### A correction to an earlier producer instruction

An earlier relay said the real name "belongs in the overlay." **That was wrong.**
`config/loader-source-overlay.yaml` maps *loader name → registered dataset id* and carries no
database name at all. If you acted on it you would have found nowhere to put the value. The
homes are the two named in step 4.

---

## 2. Why option (b) was never actually available

Your framing offered (a) adopt `[db]` company-wide, or (b) keep the alias as a deliberate
company divergence. **(b) cannot be chosen by declining to act**, for a reason independent of
the ruling:

`config/**` is **`canonical-producer`** (`PORT-MANIFEST.yaml:686-688`), and
`config/source-registry.yaml` has no overriding row — the only registry with its own row is
`config/doc-source-registry.yaml`, a different file, `per-entry`. So the producer's `[db]`
copy overwrites yours **wholesale** at every port.

Your own agent reached this and was right: *"the test pinning the alias isn't protecting a
stable divergence, it's actually pinning something fragile that a port would silently break."*
That is exactly the position. Making (b) real would require a `PORT-MANIFEST.yaml` row
changing the disposition — which correction #1 told you not to add, correctly.

**Reverting needs no gate.** Restoring the signed state is compliance, not a new decision. It
was the 2026-08-18 substitution that would have needed one: it post-dates gate
`source-registry-v2` (signed 2026-07-31), whose clauses at `gate-log.md:1075` and `:2971` are
the `[db]` grammar, and the registry file's own header still says committed ids carry `[db]`.

---

## 3. One new producer guard, and a deliberate instruction about it

The next port carries a new **Scan D** in `tests/unit/test_publish_boundary_values.py`: it
scans the tracked publishable tree for the redacted alias and fails naming the file and line.
It pins **sha256** of the token and never writes it literally — the module's own rule is that
a guard embedding the value it protects leaks it in the act of guarding. Proven to fire on
injected drift.

**Do not take Scan D until the §1 revert is complete.** `tests/**` is
evaluate-on-collision, not canonical-producer, so this is your call rather than something the
port does to you. Taken today it fails immediately on your 10 alias ids. Two sane options,
both fine:

- take it **after** the revert, where it protects you the same way it protects the producer; or
- take it **as the forcing function**, red until the revert lands — deliberate, not a surprise.

Worth noting the guard's allowance is the **trailing underscore**: `<alias>_LOGDIR` /
`_CALLER` / `_DSN` pass, the bare token fails. That allowance is temporary — ADR 0014 clause 1
(accepted 2026-08-25) already rules the env prefix dropped at the next port after acceptance.

---

## 4. The Sub-LoB label — the one genuinely open catalog question

Your C27 review was accurate on four of five points and found the gate reversal
(`gate-log.md:1678`, 2026-08-06) that the producer had only inferred. Two corrections, and the
second is the reason this section exists.

### Correction A — the reserved map ids are the wrong names

C26 reserved `sub-lob-org-unit` and `catalog-lob-reconciles-segment` (producer
`30-mappings-catalog.yaml:239, :261`, both `proposed`). You built `lob-has-sub-lob` and
`sub-lob-has-product-line`. Four names, no overlap.

The reservation's stated purpose was that *"a port collides on a deliberate placeholder
instead of silently adding a duplicate concept."* It cannot do that — it reserved names nobody
uses. The producer will retire the two dead placeholders and reserve your two real ids
instead. Nothing for you to do; recorded so the next port's ledger explains the change.

### Correction B — the label question is NOT settled, only settled for LOB

You report Sub-LoB as "BUILT and ACTIVE company-side" and treat that as closing it. The
**grain** is settled. The **label** is not, and your build has already answered it the way the
2026-08-06 reversal rejected one level up:

| | Producer | Company |
|---|---|---|
| node label | `CatalogSubLOB` (planned) | `SubLOB` (active) |
| vocab id | `catalog_has_sub_lob` | `catalog_has_sub_lob` — **same id** |
| `to_node` | `CatalogSubLOB` | `SubLOB` |
| class | `org:OrganizationalUnit` | `org:OrganizationalUnit` — agree |

This is divergence #3 from the C26 ledger (`:LOB` vs `:CatalogLOB`) repeating one level down.
The reversal resolved it for LOB by adopting the producer's `Catalog`-prefixed label; Sub-LoB
went the other way.

**It is not a port-time break** — and an earlier producer note that said the guard "goes red
on the next port either way" was wrong. `drydocs_core/ontology/relationship_vocabulary/**` is
**`per-entry`**, and its entry rule is explicit: *"NEVER downgrade a consumer entry whose
status is active (or a node class a live loader depends on) to the producer's
planned/deprecated."* Your entry is active with `sub_lobs.cypher` behind it; the producer's is
planned. The merge keeps yours. No duplicate, no `FragmentSourceError`.

**What it is instead is a divergence with no expiry.** After every port you hold `SubLOB` and
the producer holds `CatalogSubLOB` planned, indefinitely — two labels for one concept, which
is precisely what the LOB reversal was run to end.

### Three ways out, and the producer's position

1. **Company relabels `SubLOB` → `CatalogSubLOB`**, keeps the vocab id, producer flips its
   planned entry active. One shape both sides. Costs you a relabel of a build you just did.
   **This is the producer's recommendation**, on the LOB precedent alone.
2. **Company renames its vocab id** to something company-scoped and keeps `SubLOB`. Removes
   any id ambiguity but freezes the two-label divergence permanently.
3. **Producer adopts `SubLOB`**, retiring its `CatalogSubLOB` reservation. Consistent within
   Sub-LoB, inconsistent with the LOB ruling made six weeks earlier.

The producer is not choosing for you and there is no gate blocking your side. What matters is
that **the choice is made deliberately and recorded in your ledger**, rather than left as the
default that (2) becomes by inaction.

---

## 5. What the producer is doing with C27

C27's premise — four interacting catalog questions riding one company gate sign-off — is
overtaken, as you said. Your conclusion to re-scope rather than relitigate is right, and
*"relitigating the settled three is exactly what the C26/C27 notes warn against"* is a fair
reading of them.

The producer is re-scoping C27 to **the Sub-LoB label ruling plus the map-id reservation
cleanup** — not down to the `app_id` alignment. `app_id` stays where it already lives on your
side (T1, Tier-B HELD, rebuild-not-migrate); pulling it into a catalog gate would give it a
second owner. The three settled items are cited as settled, with the reversal as their
authority.

Nothing in this section needs anything from you.
