# Writing style — U.S. business-technical English

**Provenance:** SME directive, 2026-08-03, after the executive overview's idioms
("spine", "planes") failed the readability test with its own audience. Applies to
**all NEW prose Claude writes** in this repo and to outward-facing rewrites (L22).

**Scope fence (read before sweeping):** this guide governs PROSE. It does not
rename repo **mechanisms**: `confirmed` is a HITL gate status value; the
port-prompt numbers its rules as guardrails. Renaming a mechanism is a structural
decision (ADR or gate), never a style edit. When prose must reference a mechanism,
use the mechanism's real name and explain it in plain terms — do not paraphrase
identifiers.

**SME-approved exception (2026-08-03):** **"crosswalk(s)" is fine in this repo** —
it matches terminology already used internally at the company (a separate internal
service/lookup uses the term), so the audience knows it — and it is woven through
config, code, and both repos deeply enough that a rename would cost far more than
the word ever confuses. It stays OFF the avoid list here despite appearing in the
generic list below; `config/crosswalks/` and `orchestration/crosswalk.py` keep
their names with no rename question attached.

---

## Instruction set for the AI writer

Write all documentation in U.S. business-technical English, optimized for readers
from New York City to Texas. Use clear, direct, practical language. Avoid UK/EU
idioms, academic metaphors, or overly abstract phrasing.

### Tone & clarity

- Prioritize plain, concrete language over metaphor-heavy or poetic phrasing.
- Use "backbone," "core," "primary record," "source of truth" instead of UK/EU
  metaphors like "spine," "planes," or "decays."
- Keep sentences short, active, and direct.
- Favor business clarity over stylistic flourish.

### Vocabulary rules

Use American terminology:

- "lineage model" instead of "lineage plane"
- "team changes" instead of "people moving posts"
- "validated" instead of "gate-confirmed"
- "integration boundary" instead of "vendor boundary"

Avoid UK/EU phrasing such as:

- "whilst," "amongst," "per annum," "atop," "in future," "in situ," "bespoke,"
  "proper," "decays," "crosswalks," "guardrails" (unless referring to literal AWS
  guardrails — or, per the scope fence above, to this repo's mechanisms that carry
  those names)

### Structure

- Lead with the core claim, then explain the reasoning.
- Use examples grounded in execution, data, or workflow, not abstract
  organizational metaphors.
- Prefer bullet points and step-by-step logic over narrative exposition.

### Audience fit

- Assume readers are U.S. enterprise engineers, architects, and product owners.
- Write for people who value practicality, operational clarity, and
  implementation detail.
- Avoid language that feels like management consulting jargon or academic
  research.

### Consistency

- Use "backbone" or "core record" when describing the central organizing concept
  of a system.
- Use "layers," "components," "modules," "domains," instead of "planes."
- Use "execution-derived lineage" instead of "lineage re-derived on ingest."

### Examples of correct U.S. style

- "Orchestration is the backbone of the system because it reflects what actually
  ran."
- "Execution lineage stays accurate; human-declared lineage becomes outdated."
- "Each layer — data, applications, products, roles — connects to the execution
  record."

### Examples of phrasing to avoid

- "The orchestration record is the spine, and every plane attaches to it."
- "Lineage declared by a human rots."
- "Crosswalks are gate-confirmed on paper."

## Goal

Produce documentation that feels natural to U.S. readers, especially those in
NYC, Texas, and major U.S. enterprise environments. The writing should be clear,
grounded, and operational, not metaphorical or regionally idiomatic.
