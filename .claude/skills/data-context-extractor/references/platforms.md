# Target Platform Reference

These are the platform types that appear as `DataAsset.platform` property values
in the DryDocs graph. They are NEVER graph node labels — always a string property
on `:DataAsset` and `:ControlMJob`.

---

## Supported platform values

| platform | Description | Common format values | DataHub dataPlatform |
|---|---|---|---|
| `oracle` | Oracle Database (psgmgr read-only or writable target) | TABLE, VIEW | `urn:li:dataPlatform:{oracle}` |
| `snowflake` | Snowflake cloud data warehouse | TABLE, VIEW, STREAM | `urn:li:dataPlatform:{snowflake}` |
| `teradata` | Teradata data warehouse | TABLE, VIEW | `urn:li:dataPlatform:{teradata}` |
| `s3` | AWS S3 object storage | FILE, STREAM | `urn:li:dataPlatform:{s3}` |
| `sqlserver` | Microsoft SQL Server | TABLE, VIEW | `urn:li:dataPlatform:{sqlserver}` |
| `linux` | Linux filesystem (SFTP landing zone, local files) | FILE | `urn:li:dataPlatform:{linux}` |
| `document` | Reference documents (PDF annual reports, 10-K filings, org charts) | PDF, METRICS | local only — no DataHub platform |

**Document classification drives the target database and sanitization:**

| Document type | Classification | Trust | Target DB | Sanitize? |
|---|---|---|---|---|
| Public annual reports, 10-K SEC filings | External | VERBATIM / GROUNDED | `drydocs` | No — public domain; cite `source_url` |
| Internal slide decks, design docs, org charts | Internal-Public | SYNTHESIZED | `ddcontext` | Yes — omit internal names before committing |
| Internal-confidential documents | Internal-Confidential | SYNTHESIZED | `ddcontext` | Never commit even sanitized |

> **External documents** (annual reports, SEC filings, public vendor docs) are in the
> public domain. They carry `classification: External`, require no sanitization, and
> their content can be loaded directly into `drydocs`. Extract with `trust: VERBATIM`
> for direct quotes or `trust: GROUNDED` for derived/calculated facts. Always add
> `source_url` pointing to the public source.
>
> **Internal documents** carry `trust: SYNTHESIZED` and always target `ddcontext`.
> Promotion to `drydocs` requires HITL gate confirmation.

---

## DataAsset URN format

```
urn:drydocs:dataasset:{platform}:{namespace}:{name}
```

**Examples (sanitized — replace placeholders with real values in internal file):**
```
urn:drydocs:dataasset:snowflake:<schema>:<TABLE_NAME>
urn:drydocs:dataasset:oracle:<schema>:<VIEW_NAME>
urn:drydocs:dataasset:s3:<bucket-name>/<prefix>:<filename-pattern>
urn:drydocs:dataasset:teradata:<database>:<TABLE_NAME>
urn:drydocs:dataasset:sqlserver:<database>.<schema>:<TABLE_NAME>
urn:drydocs:dataasset:linux:<host-path>:<filename-pattern>
urn:drydocs:dataasset:document:<org-namespace>:<document-name>   ← Mode C / ddcontext only
```

---

## AppDataFlow URN format (DataHub-compatible)

```
urn:li:dataFlow:{controlm,<folder-or-jobgroup-name>,<data_center>}
```

`<data_center>` must match a `ControlMServer.name` value already in the graph.
Do not hardcode new data center names — always verify against the live graph:

```cypher
MATCH (srv:ControlMServer) RETURN srv.name ORDER BY srv.name;
```

---

## isExternalFeed vs isSourceOfRecord

| Property | `true` when | `false` when |
|---|---|---|
| `isExternalFeed` | Data originates outside the org's own Control-M jobs (vendor drop, partner S3 upload, market data feed, customer upload) | Data is produced by an internal Control-M job |
| `isSourceOfRecord` | This object is the business-authoritative, governed copy cited in reporting or compliance | This is an intermediate staging object |

**These are not mutually exclusive.** An external vendor feed can be the source of
record if it arrives unchanged and is used directly in reporting.

**Who confirms these flags:** data governance team or data owner — not the developer.

---

## Sanitization rules per platform (public repo)

These apply before writing to `docs/patterns/data-catalog/`:

| Platform | Sensitive values | Replace with |
|---|---|---|
| `oracle` | Schema names (PSGMGR, DRYDOCS_STG, etc.) | `<schema>` |
| `oracle` | SID / service name | `<sid>` |
| `snowflake` | Account identifier | `<account>` |
| `snowflake` | Database name (if internal) | `<database>` |
| `teradata` | TDPID | `<tdpid>` |
| `teradata` | Database name (if internal) | `<database>` |
| `s3` | Bucket name (if internal) | `<bucket-name>` |
| `s3` | Key prefix (if contains env/account info) | `<prefix>` |
| `sqlserver` | Server hostname | `<server>` |
| `sqlserver` | Database name (if internal) | `<database>` |
| `linux` | Hostname | `<host>` |
| `linux` | Path (if contains env/account info) | `<path>` |

**Object names** (table names, file names): sanitize if they embed internal system
names; keep if they are industry-standard or already public knowledge.

---

## Port friction note

Platform names are hardcoded strings in loader files and SQL. When porting to the
company side, platform values in staging rows must match these strings exactly.
`psgmgr` is the Oracle source — its platform value is `oracle`.
