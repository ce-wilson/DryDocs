# Review provenance — every review surface names the tree it ran against (J63)

**Status:** convention, 2026-08-30. Applies to every new review, triage, research and
port-report surface in this repo. It is a companion to
[`us-business-english.md`](us-business-english.md): that one governs how the prose reads, this
one governs what the prose is *about*.

---

## The rule

A review, triage or research artifact **states the tree it ran against** in its front matter:

| Field | What it holds |
|---|---|
| `reviewed_commit` | the full or short SHA the reading was done at |
| `reviewed_branch` | the branch that SHA sat on |
| `reviewed_port_base` | the most recent `port-base-*` tag reachable from it, or `n/a` for a producer-only surface |
| `venue` | the machine, and where relevant the container and database (J18) |

That is the whole mechanism. It is **provenance, not method** — nothing here tells a reviewer
how to read, and nothing here would have changed a single observation any of the three failures
below actually made.

## Why — three instances, and the cost is the framing, not the facts

A review run against an un-ported or stale checkout **manufactures defects**. Three times now:

1. **The 2026-08-28 bootstrap triage** reported the refresh verbs as exactly backwards. All
   three are registered on producer `main`, with the older verb kept as a deprecated alias
   delegating to them (G79, 2026-08-23).
2. **The same triage** called eight commands unregistered. Seven of them exist here.
3. **An earlier review** recorded six wrong facts from a checkout predating the S8, S13, G78 and
   G79 work.

**Every observation was correct for the tree it ran on. The defect framing was not.** With the
stamp, *absent here* reads as **not yet ported** rather than **broken**, and that is the entire
difference between a finding and a false alarm.

## The irony, written down because it prevents the wrong fix

Reading the importable object faithfully — the J37 rule, and the right rule — **still reports a
stale tree faithfully.** A method rule cannot close this gap, because the method was never
wrong. The next reviewer who hits this will reach for the method rule again unless this
paragraph is here; that is why it is here rather than left as something a careful reader would
work out.

## Where the stamp lives — decided once

A convention with no list is a convention nobody applies. These are the surfaces:

| Surface | Where the stamp goes |
|---|---|
| `docs/design/*-review.md` | the `front-matter` anchor block, as a `Reviewed at:` bullet |
| `internal/research/*.md`, triage transcriptions | the YAML front matter, alongside the existing `venue_of_the_original` |
| `docs/reviews/*.md` (new ones) | the YAML front matter or the opening block, whichever the file already uses |
| `docs/port/port-prompt.md` and each PORT-REPORT | the port base is already the subject; the stamp adds the producer commit the range was cut at |

Existing files are stamped when they are next revised, not swept — a sweep would put a
present-day SHA on a document written against a different tree, which is the failure this
convention exists to prevent, applied to itself.

**Generating it.** `python scripts/review_stamp.py` prints the block for the current tree, in
either markdown-bullet or YAML form. It is a convenience and nothing depends on it.

## What producer cannot do, stated so nobody tries

**Producer cannot make the company's reviews carry this stamp.** The two repos have disjoint
histories and separate governance; a convention here binds here. What producer *can* do — and
does — is carry the stamp on its own surfaces and **describe the practice** in the port prompt,
as a description and never as a request for anything back. A company-side review arriving
without a stamp is read the way it always was; the asymmetry is normal operation, not a gap to
close.

## Not guarded, and that is deliberate

No test asserts the stamp across every surface. Asserting it repo-wide would fail on every
historical document, and back-filling those is exactly the wrong move (see above). The
convention is applied at authoring time and by review; if a guard is ever wanted, it belongs on
*newly added* files only, which is a separate item and not this one.

## Check the instrument before the subject (J76)

**The rule.** When a measurement contradicts an expectation, check the instrument before the
subject, and prefer the check that can fail loudly: read the raw exit code before parsing
anything, decode explicitly, and reconstruct a fixture from the incident at its real values
rather than authoring one. A tool that fails loudly gets fixed in minutes; a tool that fails into
"clean" gets acted on.

**Why — three incidents in one day, 2026-09-01, two machines, two people, one port.** Each has
the same shape: the instrument was broken, the artifact was fine, and the corrupted measurement
said everything was OK. Each is a default that optimises for not interrupting.

| Failure mode | What happened | What it costs | Guarded? |
|---|---|---|---|
| **Locale decoding** | A comparison script read `git show` through `subprocess.run(..., text=True)`. `text=True` decodes with the platform locale — cp1252 on that desktop — and every backlog item file holds em dashes, so the decoder substituted its way through and the script reported 18 of 25 "differences" that did not exist. | The file on disk was clean; the report said the tree was wrong. | **Yes** — `tests/unit/test_subprocess_encoding.py`: a capture that passes `text=True` or `universal_newlines=True` must pass `encoding=` too, over `scripts/`, `tests/`, `web/e2e/` and the groom-backlog skill. The allocator in `.claude/skills/groom-backlog/validate.py` is the reference shape. An exemption is `# J76: locale` on the call, with the reason. |
| **Truncated pipeline** | A sweep captured results as `... \| Select-Object -First N`. That terminates a native-command pipeline early, so `$LASTEXITCODE` reported 0 where the raw code was 1; five prefixes were declared clean on that basis and a slice was about to start on it. | A green verdict from an exit code that was never the command's. | **No** — a shell idiom no Python-side scan can see. Named here so it is recognised: read `$LASTEXITCODE` from the bare command, then truncate what you display. |
| **A fixture authored to fit the theory** | A guard was validated against fixture data written to make its author's theory true; the real pair, measured on the other tree, scored 0.08 where the fixture cleared the floor. | A guard that passes its own fixture and fails the incident it was written for. | **No** — a review property, not a mechanical one. Named here: a fixture for an incident is reconstructed from that incident at its real values, never authored to a hypothesis (J72's notes carry the worked example). |

The guarded case is the only one of the three that admits a guard cleanly; promoting the other two
to guards would be the disease this rule names — an instrument that reports "clean" for reasons of
its own.
