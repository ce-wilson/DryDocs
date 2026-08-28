<!--
INTERNAL-CONFIDENTIAL — real rosters (J14 follow-up (1), relocated 2026-07-27).
This is the VERBATIM capture formerly at docs/Product/product-overview.md
(captured 2026-06-09; raw transcription artifact — includes the generating
script's own text). It carries ~25 real names, two real SIDs, an internal DL,
and real product/cabinet mappings: internal/org/ is its designated home
(internal/README.md). The publishable stub, at knowledge/org/product-overview.md
since S14 (2026-08-27; formerly the old docs/Product path), keeps every
existing reference resolving; the PAT/catalog ontology terms it sourced are
cited from drydocs_core/schema/catalog_ontology_supplement.cypher, whose
comments now point here. Never copy values from this file outside internal/.
-->

import os

# Define the content from the provided files

product_overview = """# Product Overview: Function and Roles

This document outlines the descriptions and key responsibilities for core product roles across **Product Management**, **Product Delivery**, and **Product Portfolio Operations**.

---

| Function | Product |
| :--- | :--- |
| **Roles** | **Product Management** | **Product Delivery** | **Product Portfolio Operations** |
| **Description** | Quarterbacks of the PDLC, accountable for product strategy, roadmaps, product development, and product performance (including P&L) | Experts on change and operational readiness, drives dependency management, coordinates cross-impacts, and ensures completion of product/feature delivery | Provides support to Portfolio Quad - ensuring value delivery and performance against business objectives, enables products/portfolio to operate efficiently in the organizational ecosystems |
| **Key Responsibilities** | • Establishes the overall product strategy ensuring alignment with leadership objectives and organizational goals, while balancing prioritization between nearterm business outcomes and longer-term product development through an opiniated, durable product roadmap<br>• Drives effective and efficient end-to-end execution of a major feature or functionality to achieve healthy productivity metrics, incorporating PDLC best practices including modern development practices<br>• Leads the Quad (Product, Tech, D&A, & Design) by coordinating effective collaboration, fostering a positive culture, and ensuring all members are informed and motivated by actively communicating the context and strategy behind decisions and initiatives.<br>• Manage all product's assets (e.g., budget, headcount, and applications) in partnership with F&BM<br>• Retain, expand and evolve product through analyzing existing adoption and barriers to experience<br>• Consistently measures and tracks completion against OKRs to measure against business needs | • Ensures **E2E business, operational and change readiness** by working across APGs and with functional partners to vet that processes and capabilities are in place and coordinated<br>• Assess and help **manage intake, key dependencies, risks** and issues across PDLC<br>• Ensure quality via functional, integration and user acceptance testing and coordination across teams and APGs in the product, when needed<br>• Drive completion of Regulatory, Risk, Controls and Compliance assessments and requirements in collaboration with Product Management (e.g., NBIA, SPAA)<br>• Responsible for ensuring pre & post release activities are completed (i.e., production validations, Beta/UAT testing, reviewing and accepting open test scripts / defects, etc.)<br>• Change status of Epics and Stories in Jira to progress work along PDLC | • Provide visibility to Quad leadership on key prioritization decisions within and outside the portfolio, horizon mix, and backlog sequencing<br>• Communicate portfolio's progress and escalates risks to all stakeholders through executive-level reporting (e.g., PRs, EMRs, MBRs, Bi-Weekly emails, etc.)<br>• Monitor overall health of the portfolio through key metrics and data (i.e., business & customer outcomes, OKRs, product health metrics, capacity distribution)<br>• Provide accountability for input of clean, accurate data into systems of record (e.g., Align, Jira, PAT) by appropriate personas<br>• Provide connection between CCB Product Operations and Portfolio scaling best practices and standards within their portfolios<br>• *Exists at the portfolio and product levels (for huge products)* |
"""

technology_roles = """# Technology Standardized Roles and Responsibilities

This document outlines the standard key responsibilities for engineering and technical leadership roles, establishing clear accountability and engineering standards across the portfolio.

---

## Head of Technology

### Key Responsibilities of a **Head of Technology**:
* Manages entire portfolio of technology for a business
* Monitor portfolio-level performance across agility metrics (e.g., agility pulse engagement, staffing, tech team alignment, etc.)
* Ensure appropriate staffing of Tech Partner / teams
* Accelerate product autonomy across their portfolio
* Partner with product leadership to drive balanced prioritization (incl. modernization and efficient work delivery, minimizing tech debt and enabling reuse)

---

## Tech Partner

### Key Responsibilities of a **Tech Partner**:
* Accountable technology leader for a product
* Handles all product technology, including building, coordinating, and reuse
* Aligns and manages technology talent within the product group
* Drives technology modernization and aligns the product team with shared technology functions
* May also assume Area Tech Partner responsibilities based on product size

---

## Area Tech Partner

### Key Responsibilities of an **Area Tech Partner**:
* Owns the technical strategy for the domain; influences Area/Product roadmap
* Influence stakeholders across Product Quad and other partners
* Understands business domain and broader CCB technical landscape
* Strong executive communication skills – both technical and non-technical audiences
* Has an identifiable Area Product partner. Potentially Data and Design, too, depending on product maturity.
* Deep technical expertise. Actively engaged in platform design activities, execution strategy
* Ensure technical coherence and consistency within the Area/Product and external dependencies
* Accountable for Product delivery alignment with CCB Technology strategy
* Provide performance feedback to the team
* Manage the team, including hiring, compensation management, time management, etc.

---

## Principal Engineer

### Key Responsibilities of a **Principal Engineer**:
* Individual contributors (zero direct management)
* Solves difficult / complex engineering problems; Hands on engineering role; contributes code
* Sits outside of a scrum team; plays a matrix role within an organization with an area(s) of expertise
* One or more areas of deep subject matter expertise (specialists)
* Maintains their own Kanban boards for visibility of impact
* Ensures CCB standard implementation patterns in place by engineers
* Creates engineering frameworks, patterns, best practices that will be used by engineering teams

---

## Software Engineering Managers

### Key Responsibilities of a **Software Engineering Manager**:
* Acts as a player/coach (expected to contribute / review code)
* Provides technical oversight; responsible for the code quality produced by team
* Does regular code reviews and provides feedback to engineers
* Manages 1 or 2 teams of 5-8 engineers
* Deep technical expertise leading the development effort and actively engaged in coding activities

> **Our Goal:** We aim to have more technically skilled individuals with reduced administrative requirements, allowing managers to engage more deeply with their teams and make faster decisions. Managers are expected to commit code on a regular basis, understand and develop design patterns, attend all team ceremonies/meetings, and have regular 1:1s with their team members. Success isn't about managing more teams; it's about developing tangible skills and expertise.

---

## Software Engineers

### Key Responsibilities of a **Software Engineer**:
* Design, code, test, and deliver software to facilitate modernization and automation for our customers, clients and/or employees
* Participate in design reviews with application and platform teams throughout the life cycle to help develop software for reliability, speed and scale using leading edge technology and methodologies

---

## Product Architect

### Key Responsibilities of a **Product Architect**:
* Partner with PO and Tech Partner to shape product vision and roadmap
* Set target state architecture addressing modernization, cloud transformation and data center migration
* Drive progress to target state exposing technical debt in all decisions

---

## Site Reliability Engineering Director

### Key Responsibilities of a **Site Reliability Engineering Director**:
* Responsible for site reliability engineering team achieving strategic business results, ensuring compliance, scalability, and resilience of services to safeguard the user experience
* Partner with Tech Partner and Product Owner to identify and cross-functionally address the needs of customers or stakeholders through agreed on service level objectives and other reliability KPIs
* Guides and collaborates with stakeholders (Tech Partners, Product Owners, Product Management teams, etc.) through complex projects with broad direction to achieve individual and business/function objectives
* Influences team culture by championing innovation and change, fostering an environment where team members can share ideas and approach their work creatively to proactively address needs of customer/stakeholder and the community
* Leverages business knowledge and technical expertise to challenge assumptions, ways of working and operating models across areas of responsibility
* Partners with leadership to drive change and innovation, removing roadblocks, eliminates bureaucracy and learns from mistakes
* Manages team members' development by ensuring access to necessary resources and aligning them with mobility opportunities in line with their career aspirations

---

## Site Reliability Engineer

### Key Responsibilities of a **Site Reliability Engineer**:
* Responsible for the reliability of the system and safeguards the user experience
* Understands service level indicators and utilizes service level objectives to proactively resolve issues before they impact customers
* Troubleshoots incidents, conducts blameless post-mortems and ensures permanent closure of incidents
* Responsible for reviewing design and executing failure mode and effects analysis (FMEA) to identify and reduce potential failures and architectural risks
* Applies analytics on historical data, such as incidents and usage patterns, to predict issues and take proactive action
* Drives adoption of self-healing and resiliency patterns such as circuit breaker, bulkhead etc.
* Provide technical expertise and guidance that is focused on resiliency, observability, supportability, and testability
* Defines and drives adoption of best-in-class monitoring frameworks to accomplish end to end flow monitoring and noiseless alerting
* Designs, develops, tests and delivers software to automate manual operational work
* Facilitates maximum speed of delivery by objectively binding to error budgets of the service
"""

technology_team_types = """# Agile Product Architecture, Team Types, and Interaction Models

---

## 1. Achieving Autonomy Through Product Architecture

Agile principles highly value the autonomy of Product Owners and their teams to fully control the prioritization of their development backlog in order to meet business objectives. Anything that constrains the Product Owner from realizing autonomous capability is 'anti-agile.' Inter-dependent development at best increases the amount of collaboration, coordination, and re-planning that occurs; which is inherently inefficient. At worst, inter-dependent demand becomes a blocker resulting in a prolonged delay in the fulfillment of an Initiative of value to the Sponsoring Product.

Product Autonomy is an ideal that is attainable for most Products if development applications are architected to allow concurrent, independent development by multiple teams. Even when full autonomy cannot be achieved, there are various Interaction Types that improve Product autonomy. As Product autonomy improves, the need for inherently inefficient Dependency Management decreases.

### Sponsoring and Supporting Products Governance
* **Sponsoring Product Owners** are accountable to work with Supporting Product Owners to maximize Sponsoring Product autonomy as defined in the Interaction Type Model.
* **Supporting Product Owners** are accountable to architect applications under their ownership to achieve 'Build Using' capability where possible, and to the highest state of autonomy practical when 'Build Using' is not achievable.

---

## 2. Interaction Type Model

The following matrix outlines how application architecture impacts team dependencies, sorted from the highest to the lowest degree of product autonomy:

| Interaction Type | Scenario Description and Resource Requirements | Illustration of Interaction Type |
| :--- | :--- | :--- |
| **Build Using**<br>*(Most Desired)* | • Product B owns an application with an API that makes it easily consumable for Product A. | `[Product A]` $\rightarrow$ `[API]` $\rightarrow$ `[Product B (App Owned)]` |
| **Build In** | • Product B owns an application that is modularized to enable Product A to write in its code base.<br>• Product A requires a team with the necessary skills to write code into the module(s) owned by Product B. | `[Product A]` $\rightarrow$ `[Product B Code Base]` |
| **Build Together** | • Product B owns an application that is not API-enabled or modularized.<br>• Product A has a team with the necessary skills to write code, and there is a clear process with guidelines in place to review and ingest Product A's code. | `[Product A]` $\rightarrow$ `[Code Review / Guidelines]` $\rightarrow$ `[Product B]` |
| **Build for Me**<br>*(Least Desired)* | • Product B owns an application that is not API-enabled or modularized.<br>• There is no clear process or guidelines for code review. **Which requires Product B to use its own capacity.** | `[Product A]` $\rightarrow$ `[Product B Capacity Allocation]` |

---

## 3. The Three Tech Team Types

All development teams have an assigned Team Type, which defines how their work is structured and which Product Owner prioritizes their work. Team Types are maintained in the **PAT Product Catalog**.

* **Aligned:** The most desired Team Type that gives the Product Owner the greatest degree of autonomy. Aligned teams work primarily on Initiatives created by their Home Product. There may be occasions when an Aligned team is assigned to support the work of an external portfolio. When this occurs, the Aligned team is typically engaged and assigned through the Dependency Management Process in the same way a Flex team is engaged.
* **Dedicated:** Though they maintain an organizational alignment to their Home Product, the work of Dedicated Teams is managed exclusively out of the Sponsoring Product backlog to which it is assigned. While this provides the Sponsoring Product Owner an elevated degree of autonomy, application development constraints managed by the Home Product may impact the ability of the Sponsoring Product Owner to plan and prioritize the work of these teams. The Sponsoring Product must coordinate with the Supporting Product in planning, development, testing, and release management activities to ensure development on behalf of the Sponsoring Product does not result in unintended consequences to other users of the Supporting Product owned software application(s). However, since the Sponsoring Product Owner controls the prioritization of work for a team "Dedicated" to them, they do not use the Dependency Management Process to obtain development from such teams.
  * A Dedicated team is always aligned to a single Sponsoring Product and works exclusively out of the Sponsoring Product backlog. However, the Sponsoring Product Owner may allow **Intro-Portfolio Requests**, which are requests for support from a Dedicated team managed by them from another Product within their Portfolio. Intra-Portfolio engagement practices are at the discretion of the Portfolio and/or Product Owner, who may leverage the existing Dependency Sub-task process.
* **Flex:** When a Sponsoring Product does not have sufficient demand to warrant the creation of a Dedicated Team for their exclusive use or use across their associated Portfolio, the Sponsoring Product Owner requests the Home (Supporting) Product assist them on an ad-hoc basis. This relationship provides the least autonomy to the Sponsoring Product Owner, as their development request is prioritized against all other development requests submitted to the Home (Sponsoring) Product. The Sponsoring Product typically uses the Dependency Management Process to request participation from Supporting Product Flex teams. The Flex team type is appropriate when the majority of work performed by the team is in support of work associated with a different product or portfolio. Any work performed by the Flex team that is in support of their home product does not go through the Dependency Management Process.

### Team Type Comparison Matrix

| Governance Dimension | Aligned | Dedicated | Flex |
| :--- | :--- | :--- | :--- |
| **Organization Alignment** | Home Product | Home Product | Home Product |
| **Initiative Creation** | Home Product *** | Sponsoring Product | Sponsoring Product |
| **Backlog Alignment, Work Prioritization and Daily Mgmt.** | Home Product | Sponsoring Product * | Home Product |
| **Engagement Process** | N/A | N/A | Submit DST to Home Product |
| **Write Epics and Stories** | Home Product | Collaborative<br>(Home + Sponsoring) ** | Home Product |
| **Funding** | Home Product | Sponsoring Product | Home Product |

#### Matrix Footnotes:
* $^*_1$ Dedicated Teams may work across the portfolio to which their Sponsoring Product is associated. Intra-portfolio requests for the use of Dedicated Teams are made to the Sponsoring Product. Intra-portfolio work is managed through the Sponsoring Product backlog. All external work from a single Sponsoring backlog and their work is prioritized by the Product Owner of that backlog.
* $^{**}_2$ The Home and Sponsoring Products may collaborate to write epics and stories to be assigned to Dedicated Teams, determined by application / code dependencies and other factors related to product complexity.
* $^{***}_3$ Aligned teams work on initiatives created by the home product, but these initiatives may benefit other LOBs (as noted in the "benefitting LOB" field in JIRA). Those teams will remain listed as aligned, but we will leverage other efforts (e.g., new BOW transparency reporting) to better highlight where aligned teams are delivering work that benefits other LOBs.

---

## 4. Product Allocation Models

### Sponsoring Product (Demand Model)
The Sponsoring Product is the Product that owns an Initiative. If fulfillment of the Initiative requires contribution from Product Teams not working out of a Sponsoring Product backlog, the team from which participation is needed is referred to as a **Supporting Product**. An Initiative can have only one Sponsoring Product, but may require the contribution of multiple Supporting Products.

The Sponsoring Product owns the budget, the backlog, and the prioritization of work for their own Aligned teams, and also for teams Dedicated by other Products to them.

* **Key Attributes:**
  * Capacity Budget Ownership
  * Backlog Control
  * Work Prioritization
  * Collaboration Influence over Aligned Teams and Dedicated Teams

### Supporting (Home) Product (Fulfillment Model)
The Supporting Product owns the budget, backlog, and the prioritization of work for their own Flex teams. Sponsoring Products requiring the participation of a Supporting Product Flex team use the **Demand Management Process**.

* **Key Attributes:**
  * Capacity Budget Ownership
  * Backlog Control
  * Work Prioritization
  * Governance over Dedicated Teams and Flex Teams
"""

# Merged and Deduplicated Data & Analytics content
data_analytics_roles = """# DATA & ANALYTICS Roles and Responsibilities

*Update April 2026*

## D&A Roles and Responsibilities
CCB Data & Analytics provides data foundations, advanced analytics, and AI/ML capabilities that power Consumer & Community Banking's strategic priorities. We are laser-focused on LOB alignment, data modernization, and building an efficient AI factory — while maintaining disciplined governance and developing world-class talent.

> **Note:** *Responsibilities are mapped to the primary accountable role but do not imply exclusive ownership. All data governance actions are tracked under standard system records of operational registry (SEAL, JADE).*

---

### 1. Executive & Portfolio Layer

#### 📊 LOB/Functional Head of D&A
*Scope: Line of Business (LOB) / Functional Portfolio Management*

D&A LOB teams support the CCB businesses with dedicated analytic teams and data ownership to glean customer insights and drive business decisions. LOBs include Auto, Business Banking, Card Services, Connected Commerce, Consumer Banking, Home Lending, and Wealth Management.

* Understand LOB strategic priorities and create D&A roadmaps to address them.
* Prioritize "big rock" analytical projects and align resourcing directly to LOBs.
* Define data strategy to support business operations, objectives, and advanced analytics.
* Lead data migration efforts that provide foundations for future success.
* Own and manage all data risks and compensating controls for aligned business/function.
* Build and lead diverse teams; recruit and develop talent for future demands.
* Partner with stakeholders and build a network of peers across the business.

#### 🗄️ Portfolio Lead Data Owner
*Scope: multi-product / cross-domain portfolio*

* Provide strategic leadership on data development and delivery across a portfolio.
* Create and oversee data development plans aligned to business goals.
* Partner with Data Owners and analytics leads to prioritize critical data scope.
* Direct processes to identify, monitor, and mitigate data risks (protection, quality).
* Identify and classify critical data scope, ensuring documentation with metadata.
* Manage staff to execute data-related tasks and resolve issues.

---

### 2. Product & Domain Ownership Layer

#### 🔑 Data Owner
*Scope: single product or domain*

* Create a data roadmap within the product to support business objectives and analytics.
* Partner with stakeholders to drive understanding of data use within business areas.
* Document data quality requirements and coordinate resources for delivery.
* Develop processes to identify, monitor, and mitigate data risks, ensuring compliance.
* Build relationships with data delivery partners and data consumers.

---

### 3. Execution & Engineering Layer

#### 📋 Area Data Owner
*Scope: specific data scope (table / subject area level)*

* Execute procedures for data development to support operations and analytics.
* Work with partners to define and classify critical data scope.
* Serve as subject matter expert to drive data understanding within assigned scope.
* Execute processes to mitigate data risks, including protection and quality.
* Assist in resolving data issues and provide remediation recommendations.

#### 🔬 Analytic Lead
*Scope: Analytics Workflows, Modeling, & Insights*

* Develop OKRs and design/execute A/B testing and experimentation.
* Create and monitor performance metrics for aligned LOBs.
* Simplify customer and stakeholder experience through anticipation of friction points.
* Drive automation and adoption of ML/AI within analytics workflows.
* Invest in cross-LOB analytical initiatives (e.g., marketing automation, omnichannel personalization).
* Transform D&A through solutions that embed in business processes and deliver productivity gains.

#### 🔒 Information Owner
*Scope: Asset-level System Compliance & SEAL/JADE Registries*

An Application Information Owner is an assigned role, within SEAL, responsible for managing key Information Asset tasks related to:

* Approving Application Risk and Resiliency Assessments
* Managing Identity and Access
* Establishing Retention and Destruction Requirements
* Certifying Classifications in JADE
"""

ccb_operations = """# CCB Operations Engagement & Readiness

CCB Operations should be represented on Product Cabinets. The Operations Engagement Model for CCB Products varies depending on the Product Team and the LOB that owns the product.

Products owned by these CCB sub-LOBs are supported by **CCB Operations Cross Product Strategy Leads**.

---

## 1. CCB Operations Strategy Lead Responsibilities

* **Single Point of Contact:** Act as a single point of contact for Operations.
* **Identify Synergies & Impacts:** Identify operations impacts and cross-product synergies, opportunities, and dependencies as a result of new product features being developed.
* **Functional Guidance:** As needed, engage Ops resources with deep functional knowledge and strategic perspective to provide input and guidance to the Product Team.
* **Represent End-Users:** Represent Operations end-users' needs.
* **Product Governance:** Actively participate in Product prioritization, decisions and approvals such as MVP, roll-out plans for feature changes, defect deferral / risk acceptance, Go/No-Go.
* **SME Alignment:** Ensure the right Subject Matter Experts required to execute tasks are on Product Teams.

*For engagement please contact the appropriate Operations Strategy Lead/Cabinet Member listed below. If your product is not listed, please contact **Liz Rubinstein** at `OCPS_Full_Org@restricted.chase.com`.*

### Operations Strategy Cabinet Mapping

| LOB/Product Line | Product / Platform | Operations Strategy Cabinet Member |
| :--- | :--- | :--- |
| **Auto** | Auto Finance and Drive | Carol Harrington |
| | Auto Originations | Carol Harrington |
| **Business Banking** | SB Deposits | Carol Harrington |
| | SB Lending | Carol Harrington |
| | Business Access and Tools | Carol Harrington |
| **Card** | All Card products | Liz Rubinstein |
| **Travel and Lifestyle** | Lifestyle<br>- Dining<br>- Merchant Offers<br>- Shopping & Experiences<br><br>Travel | Paul McKelvey |
| **Consumer Banking** | ATM Channel | Juan Garcia |
| | Branch Operations | Juan Garcia |
| | Debit | Juan Garcia |
| | Firmwide Core Deposit Platform - Domestic Deposit | Juan Garcia |
| | Global Customer Platform | Juan Garcia |
| **Digital** | Communications | Mitadru Dey |
| | Connected Banking | Mohammed Parvez |
| | Self-Service Enablement | Mohammed Parvez |
| | Digital Channels | Mohammed Parvez |
| | Utilities | Mitadru Dey |
| | Personalization & Customer Insights | Mohammed Parvez |
| **Home Lending** | All HL products | Carol Harrington |
| **JMP Wealth Management** | All WM products | Carol Harrington |
| **Payments, Lending & Open Banking** | Banking Payments<br>- Pay Chase & Bills, Wires<br>- SMB & PxS<br>- QuarTZ & New Payment Rails<br><br>Commerce Payments<br><br>Tops/Tokenization<br><br>SMB Payments<br><br>Lending Innovation | Paul McKelvey |
| **Risk** | Fraud Risk | Chris Kesler |
| **Trust and Security** | Customer Identity & Authentication | Frank Gilberto |

---

## 2. CCB Operations Products & ODPM Support

Products owned by CCB Operations are supported by **Operations Delivery Project Managers (ODPMs)** from the **Change and Knowledge Management Team**.

### Operations Delivery Project Manager Responsibilities:
* May sit on the Product Cabinet to ensure visibility across area products, and provide employee readiness updates as needed
* Provide a single point of contact between the Product Team, key employee readiness contacts and delivery partners
* Ensure internal readiness needs are managed in a centralized and seamless process
* Actively participate in Initiative/Epic reviews to identify readiness impacts as a result of new product features being developed
* Open change requests and ensure a comprehensive approach to employee readiness (training, communication, procedures, etc.) and creation of roll-out plans

*For engagement please contact the assigned Operations Delivery Project Manager below. If your product is not listed, please contact **Joe A Garcia (E094720)**.*

### CCB Operations Products Alignment

| Product | ODPM |
| :--- | :--- |
| **Auto Servicing & Collections** | Angie Odell |
| **Cash & Check Management** | Sylvia Herfeldt |
| **Claims, Disputes & Fraud Operations** | Chantal Sellers |
| **Collections** | Angie Odell |
| **Customer Channel: Voice** | Rhorie Mead |
| **Fulfillment & Archive Services** | Sue Lauber |
| **Global Banking Platform** | Rhorie Mead |
| **Legal & Regulatory Control Operations** | Rhorie Mead |
| **Machine Learning & Intelligence Operations (MLIO)** | Jade Ponzo |
| **Robotics & Operations Innovation** | Joe Garcia |
| **Service** | Misty Little |
| **Workforce Planning** | Sandra Bozickovic |
| ***Non Ops* Card Lending** | Sandra Bozickovic |
| **eGain/ Chase Answers Migration** | Sandra Bozickovic |
| ***Non Ops* Digital-Customer Identity & Authentication** | Sylvia Herfeldt |
| ***Non Ops* Multi Card** | Chantal Sellers |

---

## 3. Home Lending Products & ERM Support

Products owned by Home Lending are supported by the **Agile Employee Readiness Managers (ERM)** Team covering **Consumer Originations, Correspondent and Servicing**.

### Core Guidelines:
* Home Lending ERMs should sit on the Product Cabinet to ensure visibility across area products, provide Employee Readiness update to Product Team and stakeholders, and request decisions from Product Team and stakeholders as needed.
* Home Lending ERMs ensure employees are prepared for each change delivered by the product teams following a centralized and seamless process.
* *For engagement please contact **Michelle Wesson (I687055)** to determine who is aligned with each Home Lending Product Team.*

### Home Lending Employee Readiness Manager Responsibilities:
* Provide a single-point of contact between the Product Team, business leads and support partners to determine the most appropriate roll-out plan and readiness strategy for feature changes
* Identify and tag JIRA stories that have an employee impact
* Determine the operations readiness deliverables (training, procedures, specialist communications, etc.) that must be created/updated
* Open change requests for guideline and procedure changes, job aides and other key business documents, which makes them available on Chase Answers
* Provide support to ensure surround sound for all employees across all lines of business for each product team; including training, communication and system access
"""

align_jira_standards = """# Align & Jira CCB Standards

## Hierarchy (Align & Jira)

### Characteristics of Work Hierarchy in Align and Jira
Hierarchy within Align at the work dimension is comprised of the following ticket types:

| | Theme | Initiative | Epic | Story |
| :--- | :--- | :--- | :--- | :--- |
| **Definition** | Used to differentiate an Enterprise from its competitors. They organize Initiatives based on their alignment with broader strategic goals.<br><br>Key product efforts that connect the portfolio vision to the Enterprise business strategy. | A problem to solve or an outcome to achieve; something desired or that needs to be accomplished. Made up of one or multiple Epics.<br><br>Organized around a clear piece of business intent. | Individual features or enablers which are potentially deliverable on their own. Epics are a building block of an initiative and must be tied to an Initiative. | Granular feature of an Epic. A Story represents the work (dev and test) needed to deliver a feature. Exists within Jira. |
| **Timeline** | 1 to 3 years | 1 to 6 quarterly increments | 1 quarterly increment | 1 sprint |
| **Who delivers** | Potentially delivered by multiple Team of Teams or products | Potentially delivered by multiple teams (or Team of Teams) and supported in that delivery via dependency objects | Singular Team or Team of Teams | Singular Team |

---

### Characteristics of People Hierarchy in Align
Hierarchy within Align at the People dimension is comprised of the following organizations:

| | Enterprise / LOB | Portfolio | Team of Teams | Team |
| :--- | :--- | :--- | :--- | :--- |
| **Definition** | JPMC as an entirety; inclusive of all LOBs | Products within an Enterprise (LOB). For CCB; examples would include:<br>• Connected Commerce<br>• Digital<br>• Operations | A group of Teams that PLAN and DELIVER their epics together<br><br>Synonymous with Area Product Group. | Team of dedicated individuals who focus on delivery of features/enablers at the direction of a Product Owner/Area Product Owner and with direction from an Agility Lead |

#### Team of Team Firmwide Naming Convention in Align
The naming standard follows a structured block taxonomy based on organizational boundaries.
"""

# Constructing the master document matching PXT.md navigation tree layout
master_doc = f"""# Product & Technology Transformation (PXT) Master Documentation

This comprehensive master document consolidates all core frameworks, roles, responsibilities, and operational principles across Product, Technology, Data & Analytics, and Operations. It is structured according to the master **PXT.md Navigation Tree**.

---

## 📂 Navigation Tree Layout

- [Discovery @ Chase](#discovery--chase) *(Placeholder)*
- [PXT Controls](#pxt-controls) *(Placeholder)*
- [PXT Investments](#pxt-investments) *(Placeholder)*
- [Quad Team Architecture](#quad-team-architecture) *(Placeholder)*
- [PRODUCT Roles and Responsibilities](#product-roles-and-responsibilities)
  - [Product Finance Partnership](#product-finance-partnership) *(Placeholder)*
- [Agility Roles](#agility-roles) *(Placeholder)*
- [TECHNOLOGY Roles and Responsibilities](#technology-roles-and-responsibilities)
  - [Technology Team Types](#technology-team-types)
  - [Tech Team Architecture](#tech-team-architecture) *(Placeholder)*
- [DESIGN & CX Roles and Responsibilities](#design--cx-roles-and-responsibilities) *(Placeholder)*
- [DATA & ANALYTICS Roles and Responsibilities](#data--analytics-roles-and-responsibilities)
- [Product Cabinets](#product-cabinets)
  - [CCB Operations Engagement and Readiness](#ccb-operations-engagement-and-readiness)
- [Align & Jira CCB Standards](#align--jira-ccb-standards)
  - [Hierarchy (Align & Jira)](#hierarchy-align--jira)
- [Reporting - Key tables for Align](#reporting---key-tables-for-align) *(Placeholder)*

---

## Discovery @ Chase
*(No content provided)*

---

## PXT Controls
*(No content provided)*

---

## PXT Investments
*(No content provided)*

---

## Quad Team Architecture
*(No content provided)*

---

## PRODUCT Roles and Responsibilities

{product_overview}

### Product Finance Partnership
*(No content provided)*

---

## Agility Roles
*(No content provided)*

---

## TECHNOLOGY Roles and Responsibilities

{technology_roles}

### Technology Team Types

{technology_team_types}

### Tech Team Architecture
*(No content provided)*

---

## DESIGN & CX Roles and Responsibilities
*(No content provided)*

---

## DATA & ANALYTICS Roles and Responsibilities

{data_analytics_roles}

---

## Product Cabinets

### CCB Operations Engagement and Readiness

{ccb_operations}

---

## Align & Jira CCB Standards

{align_jira_standards}

---

## Reporting - Key tables for Align
*(No content provided)*
"""
