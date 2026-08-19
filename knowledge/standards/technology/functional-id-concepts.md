---
standard: functional-id-concepts
domain: technology
taxonomy_path: technology/identity/functional-ids
governs: AppUser — the service-account identity Control-M jobs run as (run_as), its ownership model, and its relation to accounts
authority: internal-standards         # config/precedence.yaml tier 2
refines: —                            # no vendor baseline; identity-management doctrine, stated generically
applies_to_source: the firm's functional-id directory (K17 gate territory; see doc 09)
status: planned                       # captured 2026-08-19; nothing here activates an edge or a loader
trust_tier: internal / SME-supplied / sanitized
---

# Functional IDs — the concepts, stated generically

**Why this document exists.** DryDocs models the account a batch job runs as
(`:AppUser`, `prov:SoftwareAgent`) and depends on the FID → application join in a
signed gate it cannot yet satisfy (the K2 tier-2 seam; see
`docs/restructure/09-fid-identity-and-scope.md` and gate
`fid-identity-and-scope`). The concepts below are transcribed 2026-08-19 from the
firm's internal identity-management documentation and **sanitized to the mechanism**:
internal system names, product names, real ids, people, and support routes are
replaced with generic terms. Where a generic term stands in for a named internal
system, the mapping is recorded once in the **local glossary** at the end — which is
itself generic; the real names live with the evidence captures outside the tree.

## 1. What a functional id is

- A functional id (FID) is **an identifier, not an account**. It cannot log in, has
  no password, and carries no privileges or permissions of its own.
- Its purpose is to store **ownership and business purpose** for the accounts
  associated with it — the ownership of an account is *derived from the FID it is
  linked to*.
- **Multiple functional accounts can be linked to one FID** (one identity, many
  provisioned accounts across platforms).

## 2. Why FIDs exist

FIDs group associated accounts under a common business purpose, so account ownership
has one authoritative home. They are created for both:

- **Human use** — accounts shared by a team for a common purpose (shared, test, and
  training access; e.g. read-only database access, read-only server-log access).
- **Non-human use** — application-to-application / system-to-system access.

## 3. The id record and its keys

- Every functional id is associated with **two identifiers**: a **record id** in the
  current id-record system (the unique key of the new data model) and a **legacy id**
  kept for backward compatibility. Extracts may carry either or both; a mapping row
  relates them 1:1.
- FIDs are managed in a central **identity vault**, not in the legacy non-employee
  identity system that originally issued the legacy ids.
- **One FID may have one or many accounts** associated with it (§5).

Shape observed in the source material: the record id is an 8-char hex-like token; the
FID itself is a letter-plus-digits token in the same shape family as an employee id.
Neither shape is load-bearing — key on the column, never parse the shape.

## 4. The id taxonomy — where FIDs sit

The firm's identifier tree, generically:

- **Identifier**
  - **Standard id** — a person: employee, contingent worker, customer. 1:1 with a
    maintenance id where one exists.
  - **Maintenance id** — the privileged-maintenance twin of a standard id.
  - **Functional id (and its legacy-id alias)** — non-person identities, subtyped:
    **Function**, **System**, **Test**, **Training**.

The subtype matters for scope decisions: a by-application listing returns ALL
subtypes, not only the system accounts batch jobs run as.

## 5. Functional id vs accounts

The identity service holds the FID record (ownership, application assignment, plain-
English description, other metadata). The **accounts** provisioned against it live on
the platforms themselves — directory-service accounts, database accounts, mainframe
accounts, OS accounts — in a **1-to-many relationship**: one FID, accounts on many
platforms. Credentials, permissions, and account state belong to the account; purpose
and ownership belong to the FID.

Two classes of **functional account** (the accounts a FID groups):

- **System account** (also called app-to-app / service / automation / batch) — used
  by an IT system for local execution (the account the application runs as) and/or
  inter-process communication (authenticating to another process). *The Control-M
  `run_as` account is this class.*
- **Shared interactive account** (also called generic) — used by a group of people
  for a common purpose: operations/administration/support, testing, build/deploy/
  configuration, demonstration or training. Doctrine note carried from the source:
  sharing undermines accountability and should be eliminated where possible.

## 6. Ownership — the roles

- **Primary support owner** — *the* owner. Certifies the accounts associated with the
  FID at certification time, validates access, approves platform requests, and is the
  contact external systems use for authorization (password reset, certification).
  There can be only one.
- **Backup / additional support owners** — required for continuity; may take over as
  primary, approve password changes via the help desk, and edit the FID.
- **Information owner** — may modify the FID (add/delete owners, edit description).
- **Risk owner** — view-only; informational.
- Where an application assignment is present, the information and risk owners can be
  **sourced from the application catalog's contact roles** rather than named directly.

### How ownership is assigned

Two mechanisms, and *a listing does not say which one produced an assignment*:

1. **Individual** — a person's standard id is explicitly assigned as owner.
2. **Catalog role** — ownership derives from an application-catalog contact role
   (e.g. application development manager, information owner, operate manager). To
   change role-derived ownership, the *catalog record* must change; editing the FID
   assignment alone will not remove it.

### Succession (the "evergreen" process)

When a primary support owner transfers or terminates, ownership cascades down a
defined chain until a valid owner is found: backup support owner → application
owner → primary information owner → backup information owner → line manager of the
departed owner → a designated senior manager. Owners derived from a catalog role are
exempt (the role, not the person, owns the FID). Consequence for modeling:
**ownership is an as-of fact that changes without any action on the FID itself** —
a person leaving the firm rewrites ownership by process.

## 7. Consequences DryDocs must respect (mechanism, not policy)

1. **The FID is the identity spine; accounts are its instances.** Ownership questions
   join to the FID; execution questions join to the account (`run_as`).
2. **Name ≠ id.** The rest of our data joins on the *name* a job runs as; the
   directory is keyed on the *id* — and one name can be registered many times to
   different owners (measured: one agent-account name registered 171 separate times,
   each to a different manager and cost center). The grain of an HR-side extract is
   **(account id, owner)**, never the name.
3. **Ownership is as-of.** Transfers happen by process (succession, catalog-role
   changes) with no event visible in a single extract; detecting them requires dated
   snapshots (gate §B3's ruling territory).
4. **A by-application listing over-returns.** It contains every FID subtype for every
   environment of that application, including ids used to connect *to other
   applications*, app-to-app connection ids, and human shared accounts. Filtering to
   the system-account subtype is a scope decision the K17 gate rules, not a default.

## Local glossary (generic ↔ role it plays here)

| Generic term used above | What it is |
|---|---|
| id-record system / record id | the current system of record for functional ids and its unique key |
| legacy id | the backward-compatibility id from the retired non-employee identity system |
| identity vault | the central store where FID records are managed today |
| id-management portal | the UI where FIDs are created, updated, bulk-managed, and searched |
| id-owner application | the by-application search/report surface over the directory (read side) |
| application catalog | the firm's business-application registry and its contact roles |
| standard id | a person's enterprise id |

Real system names, ids, and people appear only in the evidence captures, which live
outside the repo tree under the data root (`fid/screenshots/`, J23 Internal), per the
G42 evidence-screenshot precedent.
