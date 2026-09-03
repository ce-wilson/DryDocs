# Test case: the smuggled dot — a value of `.` with no name a human would search for

classification: Internal-Public. Mechanism only — the prefixes, teams and file names below are placeholder shapes.
transcribed: 2026-09-03, from the producer's own working notes on Control-M variables (page dated 2025-04-28),
  written while parsing `CMD_LINE` with SQL. The verbatim record is machine-local:
  `internal-local/research/2025-04-28-controlm-variables-onenote-transcript.md` (desktop). Cite the file, never the capture.
checked_against: origin/main `dbd13170`; live graph = desktop, container `neo4jtest`, database `drydocs`.
exercises: the context search itself — getting from the words a human has ("period", "dot", "the value is just `.`")
  to the concept the repo and the vendor already name; research-probe-discipline §6 (read the terms ledger before
  decoding); CLAUDE.md §2 (consult the platform reference before writing code).

## 1. The scenario

An analyst is parsing job command lines and their variables with SQL. Two things make no sense:

| what the extract shows                                   | who                | the analyst's question                    |
|----------------------------------------------------------|--------------------|-------------------------------------------|
| a variable `FILE_NM_SUFFIX` whose entire value is `.`    | one team, twice    | "why would anyone store a period?"        |
| `<prefix>_%%DAT_FILE_DT_FMT..txt` — two dots before `txt`| a second team      | "is `..` a typo?"                         |
| a date variable whose value ends in a dot: `%%$OYEAR.%%OMONTH.` | the same second team | "why the trailing period?"       |

The analyst has no name for the feature. They think in grammar terms and search for "period",
"dot", "concatenate", or the literal value `.`. An agent, asked later, coins its own word for it.
The search has to land on the one concept all three rows share.

## 2. The concept, and the names it already has

**Vendor concept.** In a Control-M variable expression a single period immediately after a variable
name is the **concatenation delimiter**: it terminates the name and is consumed, never emitted.
`%%A.%%B` yields `<A><B>`. A literal dot therefore has to come from somewhere else — either a
variable *value* (`FILE_NM_SUFFIX` = `.`), or the `..` escape, where the first dot terminates the
name and the second survives.

**This repo's names for it,** which the search must reach:

| where                                                                      | name it uses                                 |
|----------------------------------------------------------------------------|----------------------------------------------|
| `internal/remediation/standards-rules-registry.md` R1                      | "No dot-smuggling (punctuation-as-value)"    |
| `knowledge/standards/technology/controlm-greenfield-job-standard.md` (§ after the file-name variables) | "dot-smuggling"; "`..` is correct, not a typo" |
| `knowledge/standards/technology/description-field-metadata-plan.md` hazard 1 | "Concatenation-dot ambiguity"; SME 2026-06-11: pattern-based detection, never name-based |
| `drydocs_core/orchestration/controlm/resolver.py` docstring                | "Concatenation delimiter"; "smuggled-dot pattern" |
| `drydocs_core/orchestration/controlm/variables.py` (`value_is_delimiter`)  | "Dot-smuggling detector"                     |
| `drydocs_remediation/detect.py` (`DOT_SMUGGLING_RULE_ID = "R1"`)           | the M0 detector                              |

So the answer to "what is this called" is: the vendor calls the period a concatenation delimiter;
this repo calls the bare-dot value **dot-smuggling** and tracks it as remediation rule R1. The two
teams in §1 are doing two different things: team 1 smuggles (R1 applies); team 2 uses the vendor's
`..` escape, which the greenfield standard permits and R1 does not flag.

## 3. What the search finds, by path

- **In-session agent.** A grep for `smuggl`, `concatenat` or `delimiter` across `knowledge/standards/`,
  `internal/remediation/` and `drydocs_core/orchestration/controlm/` reaches every row in §2. A grep for
  `period` reaches none of them — the repo's prose says "dot". The terms ledger (research-probe-discipline
  §6) is where "period → dot-smuggling" should be recorded once, so the next session does not rediscover it.
- **Vendor reference in the tree.** `external/orchestration/bmc-controlm/controlm-variables.md` has a
  "Variable Concatenation" section, but it shows `%%APPLIC_%%DATE_%%TIME` with underscores and never
  states the period rule. That section is in the file's SYNTHESIZED / SaaS-derived tier by the file's own
  banner. The rule this case turns on is **not in the vendor corpus as held**; it is held in the internal
  standards and the resolver, with an SME confirmation dated 2026-06-11 for the `%%A.%%B` half.
- **Console `/ask`** (checked 2026-09-03; desktop, `neo4jtest`, `drydocs`). The loaded `bmc-docs` corpus
  has three chunks mentioning concatenation, all in `controlm-variables`, none stating the rule, and the
  chunk holding the synthesized concatenation section is loaded at `GROUNDED` (the document default; the
  file's banner says otherwise). The standards under `knowledge/` are not loaded as documents. The console
  arm cannot answer this case today.

## 4. The half that is still open — and this page is evidence for it

Rule R10 in the registry, "Concatenation-dot correctness", records the `%%var.%%var` half as live and
the `%%var.text` half as **pending B1**. The resolver implements only the first: it consumes a period
only when `%%` follows it (`_consume_delimiter`), and its docstring says the `..` escape "is not handled
here (this shop smuggles dots via values, not `..`)".

The page in §1 shows the shop does both. Run through the resolver as it stands (2026-09-03):

| shape                                                      | resolver output                   | expected if a single period after a name is always consumed |
|------------------------------------------------------------|-----------------------------------|--------------------------------------------------------------|
| team 1: `%%PFX.%%DT.%%SFX.%%EXT` with `SFX` = `.`          | `<pfx>{ODATE}.txt`                | same — correct                                               |
| team 2: `<pfx>_%%DAT_FILE_DT_FMT..txt`, value `%%$OYEAR.%%OMONTH.` | `<pfx>_{OYEAR}{OMONTH}...txt` | `<pfx>_{OYEAR}{OMONTH}.txt`                             |
| the greenfield standard's own `%%FILE_PREFIX.%%FILE_BUSINESS_DATE..txt` | `<pfx>{ODATE}..txt`   | `<pfx>{ODATE}.txt`                                           |

Team 2's spelling — `..txt` plus a trailing dot on the date variable — is only coherent under the wider
rule, and the greenfield standard (SME-ruled 2026-08-11) documents `..` on exactly that reasoning. That
is the B1 evidence R10 was waiting for. It is recorded here as a finding for the SME and R10, not as a
resolver change: the rule is the ontology's to confirm, and the fix is one item, not a side effect of a
test case.

## 5. Pass / fail

PASS when the answer does all of the following:

1. Names the vendor concept: the period after a variable name is the concatenation delimiter and is consumed.
2. Names the repo's term, **dot-smuggling**, and cites at least one of: rule R1, the greenfield job
   standard, the metadata plan's hazard 1, the resolver docstring.
3. Distinguishes the bare-dot value (a smuggle, R1) from the `..` escape (the vendor's literal period,
   permitted by the standard) — and does not call team 2's `..` a typo or a defect.
4. Says detection is pattern-based (any value that is wholly punctuation), never by variable name,
   because teams invent their own names for the same trick.
5. Notes that the vendor page in the corpus does not state the period rule, so the citation is to the
   internal standards and the resolver, not to the vendor file.
6. If it touches the `%%var.text` half, marks it open (R10, pending B1) rather than asserting either behavior.

FAIL when the answer explains the `.` as a literal, calls `..` a typo, proposes splitting `CMD_LINE` on
`.` in SQL, or invents a name without connecting it to dot-smuggling / R1.

## 6. Why SQL could not parse it

A text-level parser cannot tell the operator dot from the literal dot: the same character is an operator
when it follows a variable name and a literal everywhere else, and the literal may arrive from a variable's
value at resolution time. That is why `resolve_command_line` in the resolver is declared the one place
substitution happens ("no caller may re-implement substitution"), and why R1's detector reads the
resolved variable, not the command text. The SQL approach was not wrong in its details; it was working
at the wrong layer.
