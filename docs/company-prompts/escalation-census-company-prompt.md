# Company-side prompt — the CM_ESCALATION_DB census: keep the work, move where it lives

> Producer-drafted 2026-08-25 for the company-side assistant. Paste or read whole.
> **Your reasoning was checked producer-side and it holds.** You asked whether
> CM_ESCALATION_DB was already registered, you got the right answer, you correctly
> refused to put it in `psgmgr.yaml`, and your stated reason — the doc-08 drift guard
> requires every ledger object to be exercised by a loader SQL — was verified
> independently against `tests/unit/test_source_mapping_drift.py`. It is exactly right.
>
> Two problems, neither of them about the census itself. One is a file that cannot hold
> your edit. One is a value in an id that should not be there.
>
> **Everything here stays in YOUR tree and YOUR ledger. Nothing in this prompt sends
> anything to the producer, and no reply, sha or figure is wanted back.** Guardrails
> stand: nothing pushes to the producer remote.

## 0. The confirmation you asked for, so it is not re-derived

Not a new feed. `seal@[db].psgmgr.cm_escalation_db` has been registered since the **N9
build, 2026-07-31**, as gate `source-registry-v2`'s worked example of the replica id
GRAMMAR — `confirmed: false`, `adapter: ~`, `feeds_taxonomy: []`. **No backlog item
builds it.** Five items mention it and none is an ingest: N7 and N9 (the gate and the
build that registered it), J13 (publish-boundary identifier class 3, ruled 2026-08-11),
J32 (a worked instance of registration ≠ attribution), and N10 — whose census of the
nine unconfirmed rows already classified this one as **a third kind**: registered, not a
feed, and not wiring-pending either.

## 1. Your census is on a file the port overwrites — this is the one that costs work

`config/source-registry.yaml` has **no row in `PORT-MANIFEST.yaml`**. Only
`config/doc-source-registry.yaml` has its own row. So it falls to the `config/**`
default, which is **`canonical-producer`**: at the next port you take the producer's copy
wholesale and your census paragraph is gone.

**N10 already argued this exact asymmetry**, for one field on one row:

> the company's `cm_hosts` wiring hold is OVERWRITTEN by the producer's
> `confirmed: true` at every port and survives only because a human pinned it and armed
> a re-arm trigger

That was one boolean. This is a whole census.

**What has been done about it, so you do not repeat the work.** The same census — 30-column
TABLE, 934,402 rows, the `EJOBNAME` join key, the three-triad routing shape, the
`ESPECIALINSTRUCTIONS` VARCHAR2(4000) field — is now recorded on the **producer's** copy of
that row, which is the direction the port actually carries. It will arrive in your tree at
the next port on its own.

**Your action:** keep your local copy if it is useful to you now — having it beats not —
but **record in your ledger that it is temporary and that the producer copy is the one that
survives**, so a later session does not read its disappearance as a port defect. Do not
add a manifest row to protect it; `source-registry.yaml` being canonical-producer is the
correct disposition and is not what needs changing.

## 2. The id carries the real database name — correct it to the placeholder

Your row reads `seal@<the real database name>.psgmgr.cm_escalation_db`. The producer's
reads **`seal@[db].psgmgr.cm_escalation_db`**.

`[db]` is not a stylistic choice and not an oversight. It is the **signed N9 grammar**:
gate `source-registry-v2` ruled the replica id shape at Q1 as
`{origin}@{db}.{schema}.{table}` with the **database redacted and schema.table published**,
and J13 class 3 (ruled 2026-08-11) turned that into the standing publish-boundary answer
for these identifiers — *"NO SWEEP OWED — already covered by the SIGNED N9
source-registry-v2 id grammar, which redacts the database and publishes schema.table."*
The literal `[db]` string is pinned in `tests/unit/test_source_registry.py`, both for this
row and for the four `controlm@[db].psgmgr.*` rows.

**Your action:** change the id's `{db}` segment back to the literal `[db]`. Then check the
same slot on your other `psgmgr` rows — the `controlm@` set, `hr@`, and the staging row —
because if this one was substituted, they may have been too.

**Two things to keep straight while you do it:**

- **This is a rename with dependencies, not an edit.** An id string is pinned by any
  retired row's `replaced_by` list and by the registry guard. Change it in one place and
  the guards fail; change it everywhere in one commit and they pass. That coupling is
  deliberate.
- **The real value is not lost, it now has a home.** It is documented producer-side in
  `internal/standards/technology/database-inventory.md` — the values twin for the `{db}`
  slot, the same artifact `data-center-inventory.md` is for the `P`→`T` swap. Until that
  file existed, ten shipped ids redacted a value nothing recorded, which is a gap shaped
  like a control. If you keep a company-side equivalent, that is where your copy belongs —
  not in the registry row.

## 3. What NOT to do next, and why it is not caution for its own sake

You offered to start the add-source-object onboarding flow — profile → column ledger →
ontology proposal → HITL gate → extract SQL. **Do not start it.** Three things are unruled,
and each one would make the ledger a transcription of decisions nobody has taken:

1. **The gate that would authorize the field is not signed.** `email-dl-contact-point`
   names `ESPECIALINSTRUCTIONS` as the candidate authoritative source for job→DL
   notification wiring. Its only gate-log entry is a **2026-08-12 `RECORD`**, and a RECORD
   is not a sign-off.
2. **The row's own `origin: seal` is under review.** Its notes say so: `ECOMPONENT = SEAL`
   is a COLUMN VALUE, not provenance, and re-keying to `controlm@[db].psgmgr.cm_escalation_db`
   is a coordinated change, not an edit.
3. **K7 has already ruled what this table may not do.** Gate `seal-app-ref-edge-reshape`
   signed 24/24 on 2026-08-03: attribution grain is FOLDER-level. The `EJOBNAME` join is
   JOB grain. A SEAL link read from here **supplements** the human folder→application
   mapping and **never authors it** — the row's own SME correction of 2026-08-17 says
   treating it as an attribution source would reinstate exactly the model that ruling
   closed.

A census is a FACT and records now. A column-disposition ledger is a set of DECISIONS about
where each column lands, and those are gate work.

## 4. One thing worth checking on your side, briefly

The drift guard's loader-SQL invariant is right and should stay. But it means a
**registered-not-loaded** object has nowhere structured for its column inventory to live —
yours went into a prose `notes:` block, which no `census_failures()` reconciles and no drift
check reads. That is captured producer-side as an open question (a census-only object class
the drift guard SKIPS *because* the object is registered-not-loaded, with the skip stated
rather than implied). **Do not solve it locally by loosening the guard.** If you hit the
same wall on another loaderless object, note it in your ledger and it will be ruled once,
in one place.

## 5. Checklist

- [ ] `{db}` segment restored to the literal `[db]` on the escalation row
- [ ] same slot checked on the other `psgmgr` rows (`controlm@` set, `hr@`, staging)
- [ ] registry guards + generated-artifact determinism guards green after the change
- [ ] `enforcement-matrix.json` regenerated (it embeds the registry)
- [ ] ledger records that the local census note is TEMPORARY and the producer copy is the
      one that survives the next port
- [ ] onboarding flow NOT started; the three unruled items above are why
