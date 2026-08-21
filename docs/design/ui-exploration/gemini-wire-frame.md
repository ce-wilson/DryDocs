Here are the expanded wireframe specifications for the **DryDocs Landing Page**. This deep dive expands the initial concept into a full, detailed page layout with alternative options and tailored component lists.

### Primary View: [EXPANDED LANDING PAGE OVERVIEW]

This detailed wireframe expands the "big picture" of image_14.png into a cohesive main page.

#### A: [ENHANCED HERO BANNER]

* **Purpose:** Provide full enterprise lineage context immediately upon entry.
* **Wireframe:** The hero area is larger, featuring a complex, consolidated lineage graph visualization (a blend of all drill-down panels into one unified schematic). This graph shows multi-interconnected sources (e.g., `[AWS RDS]`, `[GitLab]`) and consumers (`[Prometheus]`, `[Tableau]`), complete with simplified health indicators and change flags.
* **Headline:** `[DRYDOCS: YOUR ENTERPRISE DEVOPS KNOWLEDGE GRAPH]`
* **Key Benefit Icons:** Now four cards: `[Automated Discovery]`, `[Impact Analysis]`, `[Governance & Posture]`, and `[Change Management]`.
* **Primary CTA:** `[Explore Deep Lineage Deeply]`

#### B: [INTERACTIVE LINEAGE EXPLORATION SECTION]

* **Purpose:** Allow users to trace specific paths without deep drilling.
* **Wireframe:** A new dedicated section with simplified, clickable versions of the graphs seen in image_14.png (`[Tower Auto (Prod)]`, `[Data Lineage Pipeline]`, `[Global Lineage Overview]`).
* **Interactivity Cue:** A prominent note: "Click Nodes to Trace Lineage".

#### C: [POSTURE & GOVERNANCE PANEL]

* **Purpose:** Show governance status at-a-glance.
* **Wireframe:** A consolidated side panel `[Posture & Governance]` with controls like `[Audit Log]`, `[Compliance Status]`, `[Risk Score]`.

---

### SPECIFICATIONS & NOTES

These specifications are tailored specifically for rendering the *Landing Page*.

#### [VISUAL LANGUAGE]

* **Style:** Low-Fidelity, Schematic Wireframe (as pictured).
* **Palette:** Dark schematic grid background with light blue/teal accent.
* **Elements:** Clean lines, defined boxes, generic shape placeholders.
* **Cues:** Interactivity and hierarchical depth are highlighted via line weight and subtle teal accents.
* **Icons:** Standardized, outlined, generic placeholders.

#### [UX REACT COMPONENTS] (Tailored to Landing Page)

* `[DryDocsGlobalHeader]`
* `[DryDocsEnhancedHero]`
* `[BenefitCards]`
* `[LineageExplorerGraph]`
* `[PostureGovernancePanel]`
* `[InteractiveGraphNode]`
* `[LineagePathTracer]`
* `[UserOnboardingChecklist]` (new onboarding state)

---

### ALTERNATIVE LAYOUT OPTIONS (for the Landing Page)

#### Option 1: [THE TIMELINE-FIRST VIEW]

*  wireframe: The hero area is dominated by a `[System Timeline]`, allowing users to explore system state changes over time first, then trace lineage.
* **Description:** organized by system change timeline, with linked events.

#### Option 2: [THE MASSIVE-GRAPH VIEW]

*  wireframe: A single, immersive hero graph occupies 80% of the screen above the fold.
* **Description:** showing the landing page with a single, immense hero graph occupying the hero area.

#### Option 3: [THE ROLE-BASED ACCESS VIEW]

*  wireframe: multiple tailored entry points (e.g., [SRE View], [Dev View], [QA View], [Data Analyst View]) are shown prominently below a smaller hero.
* **Description:** showing different starting points based on user role (e.g., SRE, Dev, QA, Analyst).