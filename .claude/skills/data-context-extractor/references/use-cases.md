# DryDocs Domain Interview — Use Case Questions

[TO-BE-UPDATED: this file contains the seed use case questions for DryDocs domain
interviews. Replace every `[ANSWER]` placeholder with domain-specific answers during
or after the interview. Tag remaining unknowns as `[TO-BE-UPDATED]` for follow-up.]

These 7 questions drive every domain interview regardless of mode (Platform or
Application). For each question, the interviewer captures:
- Which `ControlMJob`(s) are involved
- Which `DataAsset`(s) are the inputs (`USED`) and outputs (`GENERATED`)
- Which `Application` (SEAL ID) owns the flow
- Which platform(s) are traversed

---

## UC1 — "We haven't received a file" (Customer)

**Ask the domain expert:**
"When a file doesn't arrive, which Control-M jobs are supposed to deliver it to
this platform? What conditions gate the downstream load? Where does the file
originate?"

**Graph traversal this answers:**
`FileWatcher job → REQUIRES_IN_CONDITION → Conditions → upstream blockers
→ Application + DevTeam`

**[TO-BE-UPDATED: fill during interview]**
- Jobs that deliver files to `<platform>`: [ANSWER]
- FileWatcher jobs that gate downstream loads: [ANSWER]
- Common upstream blockers (conditions not raised): [ANSWER]
- DataAsset nodes (the files): `{name: <filename-pattern>, platform: '<source>', isExternalFeed: true}`
- Cypher starting point: `MATCH (j:ControlMJob)-[:GENERATED]->(a:DataAsset {format:'FILE', isExternalFeed:true})`

---

## UC2 — "Why hasn't this table loaded" (Customer)

**Ask the domain expert:**
"When a target table on this platform isn't populated, which Control-M jobs write
to it? What do those jobs depend on? What's the most common point of failure?"

**Graph traversal this answers:**
`ControlMJob -[:GENERATED]-> DataAsset {platform, format:'TABLE'}
→ job dependencies (REQUIRES_IN_CONDITION) → stalled predecessor`

**[TO-BE-UPDATED: fill during interview]**
- Jobs that write to tables on `<platform>`: [ANSWER]
- Tables most commonly cited in incidents: [ANSWER]
- Typical prerequisite chains (N conditions deep): [ANSWER]
- DataAsset nodes (tables): `{name: <table>, namespace: <schema>, platform: '<platform>', format: 'TABLE'}`
- Cypher starting point: `MATCH (j:ControlMJob)-[:GENERATED]->(a:DataAsset {format:'TABLE', platform:$platform})`

---

## UC3 — "What is the impact of this broken job" (Customer)

**Ask the domain expert:**
"If a key job on this platform fails, what downstream jobs and applications are
affected? How many hops downstream does the impact propagate?"

**Graph traversal this answers:**
`ControlMJob → EMITS_OUT_CONDITION → downstream Conditions
→ REQUIRES_IN_CONDITION → downstream ControlMJobs → Applications`

**[TO-BE-UPDATED: fill during interview]**
- High-impact jobs on `<platform>` (large blast radius): [ANSWER]
- Downstream applications typically affected: [ANSWER]
- Estimated depth of condition chain: [ANSWER] hops
- Cypher starting point: `MATCH (j:ControlMJob)-[:EMITS_OUT_CONDITION]->(c)<-[:REQUIRES_IN_CONDITION]-(downstream)`

---

## UC4 — "Which dev team supports this app" (Ops)

**Ask the domain expert:**
"For jobs on this platform, which Application (SEAL ID) owns them? Which DevTeam
is on-call? Who is the escalation contact?"

**Graph traversal this answers:**
`Application -[:HAS_MEMBERSHIP]-> Membership -[:OF_ROLE]-> Role
 Membership -[:HELD_BY]-> Employee ← DevTeam`

**[TO-BE-UPDATED: fill during interview — internal answers, gitignore]**
- Application SEAL IDs with jobs on `<platform>`: [ANSWER — internal]
- DevTeam(s) responsible: [ANSWER — internal]
- Escalation contact (Employee node): [ANSWER — internal]
- Cypher: `MATCH (app:Application {seal_id:$sealId})-[:HAS_MEMBERSHIP]->(m)-[:HELD_BY]->(e:Employee)`

---

## UC5 — "How many apps/folders do we support + counts" (Ops)

**Ask the domain expert:**
"Roughly how many distinct Applications have jobs touching this platform? How many
Control-M folders? Which data centers?"

**Graph traversal this answers:**
```cypher
MATCH (app:Application)-[:HAS_DATA_FLOW]->(:AppDataFlow)-[:ORCHESTRATES]->(j:ControlMJob)
WHERE j.platform = $platform
RETURN count(DISTINCT app) AS appCount,
       count(DISTINCT j.folder_id) AS folderCount,
       collect(DISTINCT j.data_center_id) AS dataCenters
```

**[TO-BE-UPDATED: fill during interview]**
- Estimated distinct Application count for `<platform>`: [ANSWER]
- Estimated distinct folder count: [ANSWER]
- Primary data centers involved: [ANSWER]
- Note: run the Cypher above against the live graph for authoritative counts

---

## UC6 — "What is the source of record for this dataset" (Business)

**Ask the domain expert:**
"For the key objects on this platform, which are the authoritative business source
of record? Which jobs produce them? From what upstream origins?"

**Graph traversal this answers:**
`DataAsset {isSourceOfRecord: true}
← [:GENERATED] ← ControlMJob
← [:ORCHESTRATES] ← AppDataFlow
← [:HAS_DATA_FLOW] ← Application`

**[TO-BE-UPDATED: fill during interview]**
- Source-of-record objects on `<platform>`: [ANSWER]
- Jobs that produce them (set `DataAsset.isSourceOfRecord = true`): [ANSWER]
- Upstream lineage origin (external feed?): [ANSWER]
- Cypher: `MATCH (a:DataAsset {isSourceOfRecord:true, platform:$platform})<-[:GENERATED]-(j:ControlMJob)`

---

## UC7 — "What is the end-to-end lineage for this data" (Business — DryDocs unique value)

**Ask the domain expert:**
"Trace the full path for data that ends up in `<target object on platform>`. Where
does it originate? Which platforms does it cross? Which Control-M jobs move or
transform it at each hop?"

**Graph traversal this answers — no data catalog can answer this:**
```cypher
MATCH path = (src:DataAsset {isExternalFeed: true})
             <-[:USED]-(j1:ControlMJob)-[:GENERATED]->(mid:DataAsset)
             <-[:USED]-(j2:ControlMJob)-[:GENERATED]->(tgt:DataAsset {isSourceOfRecord: true})
RETURN path,
       [n IN nodes(path) WHERE n:DataAsset | n.name + '@' + n.platform] AS platformHops
```

**[TO-BE-UPDATED: fill during interview]**
- External feed origin (platform + object): [ANSWER]
- Intermediate hops and platforms: [ANSWER]
- Final target (source of record, platform): [ANSWER]
- Platform hop sequence: `<external> → <platform1> → <platform2> → <final>`
- This is the path NO enterprise data catalog can answer — catalogs see data AT
  REST on individual platforms; DryDocs sees all hops because Control-M orchestrates
  them.

---

---

## UC8 — "Which applications belong to this business segment?" (Mode C — Segment Context)

**Ask the domain expert:**
"For segment CCB / CIB / AWM / Corp — which catalog LOBs reconcile to it?
Which product lines and products fall under those LOBs? Which SEAL applications
are owned by those products?"

**Graph traversal this answers:**
```
BusinessSegment ← [:RECONCILES_TO] ← CatalogLOB
  → [:HAS_PRODUCT_LINE] → ProductLine
  → [:HAS_PRODUCT] → Product
  → [:HAS_APPLICATION] → Application
```

**[TO-BE-UPDATED: fill during interview]**
- Segment code: [ANSWER]
- LOBs reconciling to it (with confidence): [ANSWER — internal]
- Product lines under those LOBs: [ANSWER — internal]
- SEAL application count: [ANSWER — internal]
- Cypher: see `cypher-patterns.md` Mode C, UC8

---

## UC9 — "What product lines exist under this LOB?" (Mode C — Product Hierarchy)

**Ask the domain expert:**
"For a given LOB code — what product lines does it contain? How many products
per line? How many SEAL-registered applications per product?"

**Graph traversal this answers:**
```
CatalogLOB -[:HAS_PRODUCT_LINE]-> ProductLine
           -[:HAS_PRODUCT]-> Product
           -[:HAS_APPLICATION]-> Application
```

**[TO-BE-UPDATED: fill during interview]**
- LOB code: [ANSWER]
- Product line count: [ANSWER]
- Products per line (range): [ANSWER]
- Application count per product (range): [ANSWER]
- Cypher: see `cypher-patterns.md` Mode C, UC9

---

## UC10 — "Which teams support this product?" (Mode C — Team Ownership)

**Ask the domain expert:**
"For a given product — which AreaProduct Groups sit under it? Which DevTeams
are aligned to (SUPPORTS) those APGs? Which SEAL applications does each team develop?"

**Graph traversal this answers:**
```
Product -[:HAS_AREA_PRODUCT]-> AreaProduct
        <-[:SUPPORTS {team_type}]- DevTeam
        -[:DEVELOPS]-> Application
```

**[TO-BE-UPDATED: fill during interview — internal, gitignore]**
- Product id / name: [ANSWER — internal]
- AreaProduct Groups: [ANSWER — internal]
- DevTeams with team_type (aligned / flex / dedicated): [ANSWER — internal]
- Applications each team develops: [ANSWER — internal]
- Escalation contacts (via Membership): [ANSWER — internal]
- Cypher: see `cypher-patterns.md` Mode C, UC10

---

## UC11 — "Segment-level blast radius" (Mode C — Cross-Segment Impact)

**Ask the domain expert:**
"If jobs from segment X stall, which downstream applications in OTHER segments
are blocked? How many condition hops does the impact cross?"

**Graph traversal this answers:**
```
BusinessSegment → (LOB→Product→App→Flow→Job) -[:EMITS_OUT_CONDITION]->
  Condition <-[:REQUIRES_IN_CONDITION]- downstream Job
  → (App→Product→LOB→BusinessSegment) for the downstream segment
```

**[TO-BE-UPDATED: fill during interview]**
- Source segment: [ANSWER]
- Known cross-segment condition dependencies: [ANSWER]
- Typical depth (condition hops): [ANSWER]
- Most-impacted downstream segments: [ANSWER]
- Cypher: see `cypher-patterns.md` Mode C, UC11

---

## Interview tips

- **Mode A/B** (platform/application): Ask UC1 and UC2 first — most concrete DataAsset candidates
- **Mode C** (org hierarchy): Ask UC8 first to map segment→LOB, then drill into UC9 (product lines) and UC10 (teams)
- UC7 and UC11 are the hardest; seed them and leave `[TO-BE-UPDATED]`
- UC4, UC10 answers are internal — capture in the gitignored file only
- If a UC doesn't apply to this domain, mark `N/A — not applicable: <reason>`
- Confirm `isExternalFeed` and `isSourceOfRecord` with a data governance contact,
  not just the developer — these drive business-critical lineage queries
- **Segment metrics from public documents** (annual reports, 10-K SEC filings): `classification: External`,
  `trust: VERBATIM/GROUNDED`, set `source_url`, load directly to `drydocs` — no sanitization, no staging
- **Segment metrics from internal documents**: `trust: SYNTHESIZED`, written to `drydocs` labelled `:Uncertain`, label cleared via HITL gate
