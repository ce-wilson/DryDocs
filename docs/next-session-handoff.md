# Next-session handoff

> **Rolling file — overwrite it, do not append.** One screen of "where things stand"
> for picking the work up on the other machine. Durable state lives in
> `docs/restructure/backlog.yaml` (the claim channel) and `docs/port-prompt.md`; this
> is the narrative that git alone does not carry.
>
> **Written 2026-08-18 (laptop), producer head `d5e7966d`.**

## 1. The desktop may still be push-blocked

Unchanged from yesterday unless someone completed the browser sign-in at a desktop
session: GCM is per-machine, so the laptop's login did not unblock it. Its stranded
`5ca7dc8f` is already superseded (identical fix shipped as `63551c8`); a revived
desktop session should `git pull --rebase` and its duplicate drops as empty.

## 2. Port loop

`port-base-20260817` @ `0c355f5` remains the certified base. Everything since rides
the NEXT roll — and today added a lot: **RELAY-10** (the ServiceNow TOM build
decisions + its stub-and-enrich rider) is the piece the company session depends on;
it travels the J38 channel at the next port.

## 3. What landed today (all pushed, CI green at every commit)

- **G98 SIGNED 19/19** — the corporate-backbone gate. :Company registered
  (org:FormalOrganization), new `corporate` domain (49-local-corporate.yaml), the
  §D3 endpoint guard (`test_vocabulary_endpoints.py`, both directions, with declared
  debt lists), the §B2 agreement check in `m3-verify`.
- **G91 CLOSED 5/5** — the held planned-entry review. Keep-planned ×2 (with the
  `m3_` → `scheduler_` id migrations and the new `scheduler_runs_as` raised),
  `catalog_has_area_product` ACTIVATED, `catalog_area_product_has_dev_team`
  deprecated-redundant, and entry 5 **re-shaped onto qualified attribution**
  (superseding the K4 carve-out and C20 retention — both named in the gate log).
- **G99 DONE** — `pat_team_roles.cypher` rewritten onto the attribution shape;
  both new entries active; `membership_id` constraint dropped with its last writer
  (53 → 52).
- **The ITSM technician-group family registered** (`50-local-itsm.yaml`, `itsm`
  domain): :ServiceNowGroup + :SnowRole (SENG/ASUP), both edges planned. **G100** is
  the gate that ratifies the register and builds the OOTB lookup — build against the
  SOURCED replica feed (Idea-132), not the retiring CSVs.
- **STUB-AND-ENRICH ruled** (SME direction, gate-log RECORD 2026-08-18): the HR DB
  is ~300k and deferred, so people-referencing loads MERGE the stub :Employee on the
  SID and HR enriches later. G74 clause 2 answered in direction; G74 still owes the
  runbook harmonization, the stub property idiom, and clause 1 (REPORTS_TO).
  `pat_team_roles.cypher` flipped from strict MATCH to MERGE-stub accordingly.
- **cm_escalation_db note corrected** — job-grain SUPPLEMENTS the folder mapping,
  never authors (K7 §A1); origin/id re-key flagged under-review, deliberately not
  done. **Idea-130/131/132** inboxed (External-public corpus; the :Company finding;
  the ServiceNow extract re-sourcing).

## 4. The company session's gate (`snow-tom-responsibility`) — where it stands

§A/§D/§F/§G/§H ticked; §C ruled stub-and-enrich for Individual scope (Group half —
an unloaded :ServiceNowGroup — is load ORDER, deliberately not covered; flag or
sequence, still theirs to rule). **Open: §B grain and §E inheritance.** Producer
recommendations relayed in-chat and in RELAY-10: §B deployment-with-app-fallback
(K7 §C1 supernode reasoning, from-node class recorded on the edge); §E
authored-only with the ancestor-CI pull taken as a SEPARATE coverage decision, no
materialization (inheritance is COMPUTED, `4c0c834`).

## 4b. Working direction (SME, 2026-08-18 late)

**Producer backlog only for now — company-side grooming is paused.** Consequences:
the RELAY-11 IDEAS.md union repair becomes next-port-session work (rider on the
relay says so); K16 stays blocked (its counts are company-side); the caa0406
close-out confirmation and the snow-tom-responsibility §B/§E rulings arrive
whenever company work resumes, not before. GitHub Actions is billing-blocked
(jobs die at dispatch) — every push since `50d7831a` is locally verified only;
one green run at HEAD covers them all once billing is fixed.

## 5. Board state

**~122 todo · 4 in progress (E1, G32, Y1, G62 — all SME/gate-bound) · 1 blocked
(K16) · 316 done.** Oldest pullable unchanged; new ready items: **G100** (the ITSM
gate) and the O60-O62 UI trio.

## 6. The pattern from this session

Three times today a drafted framing failed against the code: the review file's
"all three retire together" (never an SME position), my own "OF_ROLE/HELD_BY are a
registration gap" (C8 reuse made non-registration CORRECT), and yesterday's
strict-MATCH no-stub reading (the direction went the other way within a day).
Same lesson each time: **drafted prose and even fresh code embed a side of an
unruled question — check which side before citing either as settled.** The fix that
sticks is putting the ruling where the next reader looks: the gate log, the entry
note, the relay — never the chat.
