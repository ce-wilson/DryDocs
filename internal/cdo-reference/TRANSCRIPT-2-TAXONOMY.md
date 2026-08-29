# Taxonomy — transcription set 2 of 4

*Part of the JPMC Confluence screenshot transcription set. Source screenshots live in `C:\coding\@SCREEN-SHOTS`; the unsplit master is `CONFLUENCE-TRANSCRIPT.md`.*

The firmwide Taxonomy Framework specification, plus the live CCB taxonomy reference data it governs. Screenshot groups: `taxonomy`, `taxonomy2`, `taxonomy-list`1–3 (5 shots).

---

## Contents

| Section | Source | Type | Shots |
|---|---|---|---|
| 1 | Taxonomy Framework | Confluence — `https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5772894415/Taxonomy+Framework` | 2 |
| 2 | Taxonomy Information | **Not Confluence** — `ccb-governance.gaiacloud.jpmchase.net/reference-data/taxonomies` | 3 |

---

# Taxonomy Framework

> **URL:** https://confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY/pages/5772894415/Taxonomy+Framework
> **Screenshots:** taxonomy.png, taxonomy2.png
> **Coverage:** capture begins at §4.1; §1–§4 heading not screenshotted, and the page is clipped mid-§5.1.1.

### 4.1. Open Standard Requirements

To ensure consistency and interoperability, any Taxonomy must be documented as defined in this framework. This standardization facilitates consistent integration with various tools and systems, allowing consumers to seamlessly access and interpret taxonomies.

Individual implementations do not require a manually documented diagram, but must include a machine-readable set of documentation that follows an approved framework or be approved as an exception/extension of an approved framework.

### 4.2. Standard Access Method

Whenever a publisher makes a Taxonomy available, they must implement a mechanism that allows consumers to query the metadata.

To maximize accessibility, the Taxonomy must be accessible with standard encoding, preferably UTF-8, and accessible from a non-proprietary interface, such as a REST API. This approach ensures that consumers can easily retrieve and utilize the Taxonomy, regardless of their technical environment.

### 4.3. Information to be Included in a Taxonomy

```
A) For each concept in a taxonomy, the following attributes are required unless marked:
   a. A preferred label.
   b. The taxonomy (or taxonomies) to which it belongs.
   c. The date(time) when the concept was created.
   d. The creator(s) of the concept.
   e. The unique identifier for the concept.
   f. A definition of the concept.
   g. The date(time) when the concept was last updated (required if applicable).
   h. The actor that modified the concept (required if applicable).
   i. The taxonomy of which it is a top concept (required if applicable).
   j. Any additional labeling properties (optional):
      i. One or more alternative labels that might be useful.
      ii. One or more labels that are hidden to users (e.g., in some UI), but still useful for some purpose.
   k. Any relational properties (optional):
      i. Any concept(s) which are more general "parents" of the current concept in the taxonomy.
      ii. Any concept(s) which are more specific "children" of the current concept in the taxonomy.
      iii. Any concept(s) which are considered "related" to the current concept and which do not fall into any of the previous relations in the taxonomy.
   l. Any mapping properties (optional):
      i. Any concepts in *other* taxonomies which are more general than the current concept.
      ii. Any concepts in *other* taxonomies which are more specific than the current concept.
      iii. Any concepts in *other* taxonomies which are sufficiently similar to the current concept, such that they can be used interchangeably.
      iv. Any concepts in *other* taxonomies which are equivalent to the current concept.
   m. Any additional notations (optional):
      i. Any additional information about the intended meaning or scope of the concept.
      ii. Any administrative information about the concept.
B) For each taxonomy, the following attributes are required unless marked:
   a. The label of the taxonomy.
   b. The date(time) when the taxonomy was created.
   c. The creator(s) of the taxonomy.
   d. The unique identifier for the taxonomy.
   e. A description of the taxonomy.
   f. The date(time) when the taxonomy was last updated (required if applicable).
   g. The actor that modified the taxonomy (required if applicable).
   h. Any concepts in the taxonomy which are considered the top concepts (at least one required per taxonomy).
   i. Any additional labeling properties (optional):
      i. One or more alternative labels that might be useful.
      ii. One or more labels that are hidden to users, but still useful for some purpose.
   j. Any additional notations (optional):
      i. Any additional information about the intended meaning or scope of the taxonomy.
      ii. Any administrative information about the taxonomy.
```

### 4.4. Available Open Frameworks

Within the firm, any taxonomy must adhere to the requirements detailed in this document, the Data Publishing Council-approved Taxonomy Framework.

This Framework adopts a subset of the **Simple Knowledge Organization System (SKOS)** and **Dublin Core Metadata Initiative (DCMI) Metadata Terms**.

**SKOS** is a data model for knowledge organization that produces machine-readable data for thesauri, classification schemes, subject heading schemes, and importantly, taxonomies. It is an OWL (Web Ontology Language) Full ontology, expressed in Resource Description Framework (RDF) triples; any RDF syntax, such as Turtle (TTL), JSON-LD, and RDF/XML.

**DCMI Metadata Terms** is a general purpose metadata vocabulary for describing resources of any kind.

Additional applicable properties can be used provided they do not conflict with the requirements **here**.

## 5. Taxonomy Classes and Associated Properties

The fundamental building blocks of taxonomies consist of the following:

- A particular domain
- The concepts or categories of that domain
- Any relations that exist between those concepts (e.g., parent-child)

A rudidemtnary taxonomy of mammals, for example, could have two "top" concepts, Monotremes and Therians, and two subcategories of Therians, Marsupials and Placental Mammals.

Taxonomy metadata should the creation time and creator(s) of the taxonomy, provenance information, labels, and more. Concept metadata should include information about their history, scope, relationships they have with concepts within the same taxonomy or outside of it, and any different names or labels that might facilitate their discoverability.

Taxonomies are defined by instantiating standard classes and properties, namely `skos:Concept` and `skos:ConceptScheme`. The former represent individual concepts, terms, categories, or classifications within a taxonomy, and the latter represent the taxonomy itself, as a collection of `skos:Concepts`. The required, recommended, and optional properties for those classes are described in the following sections.

### 5.1. Specifying a Concept

The basic elements of a taxonomy--individual concepts, terms, categories, classifications, etc.--are instantiated as `skos:Concepts`, which are defined below.

| `skos:Concept` | |
| --- | --- |
| **Definition** | A unit of thought, such as an idea, meaning, (categories of) objects and or events, both abstract and concrete. |
| **Properties** | `skos:prefLabel, skos:inScheme, dcterms:created, dcterms:creator, dcterms:identifier, skos:definition, dcterms:modified, jpmv:modifiedBy, skos:topConceptOf, skos:altLabel, skos:hiddenLabel, skos:broader, skos:narrower, skos:related, skos:broadMatch, skos:narrowMatch, skos:closeMatch, skos:exactMatch, skos:scopeNote, skos:editorialNote` |

#### 5.1.1. Required Concept Properties

The following are required properties for every `skos:Concept`.

| `skos:prefLabel` | |
| --- | --- |
| **Requirement section** | A) a. |
| **Definition** | Specifies the preferred lexical label for a concept or concept scheme. |
| **Domain** | `skos:Concept` or `skos:ConceptScheme` |
| **Range** | `xsd:string` |
| **Usage note** | For a single concept, there can only be **one** value for this property per language tag. For example, there cannot be two preferred labels bearing the language tag `@en`. There **MUST** be a language tag. |

| `skos:inScheme` | |
| --- | --- |
| **Requirement section** | A) b. |
| **Definition** | Indicates the concept scheme(s) to which the concept belongs. |
| **Domain** | `skos:Concept` |
| **Range** | `skos:ConceptScheme` |
| **Usage note** | Though compatible with the SKOS model, it is recommended that a concept be included in only one concept scheme. |

| `dcterms:created` | |
| --- | --- |
| **Requirement section** | A) c. |
| **Definition** | Date or dateTime of creation of the resource. |

*(clipped at the bottom of taxonomy2.png — the remaining rows of the `dcterms:created` table, e.g. Domain, Range, Usage note, and all subsequent property tables, are not captured)*

---

# Taxonomy Information  *(not Confluence — CCB Governance reference-data application)*

> **URL:** https://ccb-governance.gaiacloud.jpmchase.net/reference-data/taxonomies
> **Screenshots:** taxonomy-list.png, taxonomy-list2.png, taxonomy-list3.png

Tabs: **Customer Offering Products** | **Business Domains** | **Business Subdomains**

## Customer Offering Products

*(tab shown in taxonomy-list.png)*

| Customer Offering Product Id | Customer Offering Product Name | Event Physical Name | API Basepath Name | Description | Created Timestamp | Updated Timestamp | Created By | Effective Date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Firm | jpmc | jpmc | This is a grouping that should be used when products span any of the offerings provided by Chase, Wealth Management and Investment Banking. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 2 | CCB/Cross-LOB | ccb | ccb | This is a grouping level that should be used when products fall within 2 or more of the following categories: Auto Lending, Business Banking, Consumer Banking or Student Loan | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 3 | Business Banking | business_banking | business-banking | Business banking products which include Business Checking and Savings, Business Loans, Business Credit Lines and Merchant Services | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 4 | Consumer Banking | consumer_banking | consumer-banking | This is a grouping level which should be used when products fall within 2 or more of the following categories: Deposit Account or Safe Deposits. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 5 | CD/IRA | cd_ira | cd-ira | Time deposit products such as CD/IRAs. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 6 | Deposit Account | deposit_account | deposit-account | Deposit account products, which include: Savings Accounts, Checking Accounts and Money Market Accounts | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 7 | Safe Deposits (Boxes) | safe_deposits | safe-deposits | This product line is limited to Safe Deposit boxes. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 8 | Auto Lending | auto_lending | auto-lending | Auto financing products which include Chase Car Buying services, Auto Loans, Refinancing a car loan, and Auto leasing. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 9 | Student Loan | student_loan | student-loan | Educational financing products which includes Student loans. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 10 | Card | card | card | This is a grouping that should be used when the products supported include two or more of Credit Card, Debit Card, electronic Gift (eGift) Card, and/or Prepaid Card | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 11 | Credit Card | credit_card | credit-card | This is a grouping that should be used when the products supported include two or more of (Consumer) Personal Credit Card, Small Business Card, and/or Commercial Card. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 12 | Small Business Card | business_card | business-card | A small business credit card account is a financial account designed for small businesses, allowing them to borrow funds up to a specified credit limit for business-related expenses. The borrowed amount must be repaid monthly and may incur interest if not paid in full. Accessed via physical cards and electronic methods, these accounts offer features like expense tracking, rewards programs, and fraud protection, helping businesses manage cash flow and build credit history.  This card is issued to individuals for business use and owner is personally liable, both individually and jointly with the Company. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 13 | Personal Credit Card (Consumer) | consumer_card | consumer-card | A consumer credit card account is a personal financial account that allows individuals to borrow funds up to a set credit limit for purchases or cash withdrawals. The borrowed amount must be repaid (usually monthly) and may incur interest if not paid in full. Accessed via physical credit cards and electronic methods, these accounts offer fraud protection, credit history building, and may include additional features like rewards programs, travel insurance, or purchase protection. | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 | |
| 16 | Home Lending | home_lending | home-lending | This is a grouping level which should be used when categorizing products that belong to both Mortgages and Home Equity | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 17 | First Mortgage | first_mortgage | first-mortgage | A legal agreement by which a bank or other creditor lends money at interest in exchange for taking title of the debtor's property, with the condition that the conveyance of title becomes void upon the payment of the debt | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | 2019-09-30 |
| 18 | Home Equity | home_equity | home-equity | A home equity loan is a type of loan in which the borrower uses the equity of his or her home as collateral | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 19 | Investments | investments | investments | Investment services which are offered to consumer banking customers, which include JP Morgan Advisor Services or Online Investing which is also known as "You Invest". This product category includes products such as Insurance, Annuities, 529 Plans and IRAs (SEP, Roth) | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 20 | Merchant Services | merchant_services | merchant-services | Services and products to help merchants securely accept card transactions | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 21 | Auto Save | auto_save | auto-save | A feature which allows an account holder to specify rules for transferring money from one account to another in order to save more. | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 22 | BillPay | bill_pay | bill-pay | A service through which a customer can set up recurring payments, pay bills and transfer money from Chase.com or a mobile device. | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 23 | Car Buying Service | car_buying | car-buying | A service by which Chase customers can search for a car and see what others have paid; locate an in-stock vehicle that matches their search preferences; obtain a savings certificate which can be used with participating dealers. | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 24 | ChasePay | chase_pay | chase-pay | A Chase provided payment application created on a digital device used to interact with the Point of Sale (POS) device as a catalyst for a transaction. | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 25 | Credit Journey | credit_journey | credit-journey | | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | |
| 26 | Donor Advised Fund | donor_advised | donor-advised | A donor-advised fund (DAF) is a charitable giving vehicle administered by a public charity created to manage charitable donations on behalf of organizations, families, or individuals. | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | 2019-05-15 |

## Business Domains

*(tab shown in taxonomy-list2.png)*

| Business Domain Id | Business Domain Name | Event Physical Name | API Basepath Name | Description | Owner Name | Created Timestamp | Updated Timestamp | Created By |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Customer Services | customer | customer | Services that expose Customer-specific data for inquiry and/or maintenance. Examples: Account Relationships, Customer Combine, Customer Contact Info Change, Financial Profile, Industry Classification Inquiry, KYC, Language Preference, Privacy Preferences, Shared Secrets Maintenance, Tax ID Maintenance | Schmitter, Todd | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 2 | Sales & Relationship | sales_relationship | sales-relationship | Business Processes related to developing and executing strategies for lead and sales management and retention for prospects and customers, and establishing, retaining, and enriching relationships with partners, third parties and investors. | Medicharla, Ravi | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 3 | Marketing | marketing | marketing | Business Processes related to the activities, operational areas and processes for creating, learning, communicating, delivering and exchanging offers that have value for prospects, customers, clients and partners. | Romanelli, Rick | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 4 | Risk | risk | risk | Identification, assessment and measurement of risk - and the implementation of mechanisms to mitigate those risks. | Abate, Pio | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 5 | Fraud | fraud | fraud | Business Processes supporting the prevention, detection, remediation, and prosecution of criminal activity resulting in identity or monetary theft that victimizes Chase customers including activities related to AML, OFAC/Sanctions | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 6 | Originations | originations | originations | Business Processes related to application and document capture, decisioning, underwriting and funding for debit/credit products, investment products and/or merchant acquiring services. This includes initiation of applications from Chase and third party vendors/affiliates/partners to create new customer accounts KEYWORD: Acquisitions (Cards) | Various | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 7 | Payments | payments | payments | Services that support payment and transfer service capabilities for our customers. This includes setup / enrollment, payment requests, and payment status inquiry. These services span across multiple products / accounts. It is important to note that the activities included in this category do not include the posting of payment transactions to an account, which will be found under Transaction Processing. These services enable mobile, b2b, p2p, etc. and can have all types of payments such as QP, BP, ACH, Wires. Does not include payment posting transactions, with amounts that change balances. | Various | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 8 | Transaction Processing | transactions | transactions | Business Processes related to processing value transactions (i.e. monetary or rewards) created as a result of a customer using Chase credit or debit products or services. It is important to note that all transaction processing activities result in an accounting function (debits and credits) which will impact account balances. | Various | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 9 | Servicing | servicing | servicing | Business Processes related to establishing and fulfilling new accounts and providing individual answers, information, assistance, account and product maintenance and problem resolution related to disputes or escalated complaints. Includes attended and self service channels. | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 10 | Loyalty Management | loyalty_rewards | loyalty | Services that provide inquiry and maintenance capabilities for Reward account activity, including Rewards Summary, Balance, Transaction history (Earns and Redemptions). | Moyer, Gary | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 11 | Customer Fulfillment Services | fulfillment | fulfillment | Business processes related to preparing, packaging and shipping account documents or materials to the account holder. | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 12 | Merchant Acquiring Services | merchant_acquiring_services | acquiring-services | Services that primarily support the Acquiring side of our business and enable our Merchants to integrate with us to use our payment products and process payments through multiple channels | Shuttleworth, Ryan | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 13 | Document Management | document_management | document-management | Managing processes for document acquisition [capture/indexing of inbound documents], document generation of outbound documents, and storage/retrieval document information in support of all business functions. | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 14 | Default Management | default_management | default-management | Business Processes related to the management of non-performing credit products where Chase Customers are unable or unwilling to adhere to the repayment terms of their agreements. For products involving physical assets such as homes or auto, processes may include preservations, liquidations and repossessions. | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 15 | Shared Functions | shared_functions | shared-functions | Business Processes related to establishing and operating core business functions that span across products and channels offering economies of scale for execution across CCB. | Vieira, Joe | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 16 | Finance & Accounting | finance_accounting | finance-accounting | Business Processes related to the financial control of the business including budgeting, forecasting, accounting and settlement, reserve management and financial reporting and analytics. | Abate, Pio | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 17 | Content Management | content_management | content-management | End to end creation, approval and publication of client facing content. | Romanelli, Rick | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 18 | Management and Controls | management_controls | management-controls | Business Processes related to critical support functions that manage and control operations. These are activities which are driven by corporate decisions and functions. | Various | 2020-04-27T18:30:38Z | 2026-05-29T19:58:01Z | d607893 |
| 19 | Technology Management | technology | technology | Technology management is a comprehensive function that involves the strategic planning, implementation, and oversight of technology systems and processes within an organization. It encompasses various specialized functions, including build management, deployment management, runtime management, design management, and test management. These functions collectively ensure the efficient development, deployment, operation, and maintenance of software applications and infrastructure. The goal of technology management is to align technology initiatives with organizational objectives, optimize resource utilization, enhance system performance, and ensure the delivery of high-quality, reliable technology solutions. | Various | 2025-05-07T17:03:21Z | 2026-05-29T19:58:01Z | |

## Business Subdomains

*(tab shown in taxonomy-list3.png. The table is scrolled: the header row and the upper portion of the first visible row are cut off above the top of the shot. Column labels below are inferred from the Business Domains tab and the visible data.)*

| Business Subdomain Id | Business Subdomain Name | Event Physical Name | API Basepath Name | Description | Business Domain Id | Effective Date | Created Timestamp | Updated Timestamp | Created By | Business Domain Name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| *(clipped)* | ...Management | *(clipped)* | contracts | ...relationships with those who participate in the sales process. Keywords: Pricing tiers, Profit Sharing, Cost Sharing, Interchange, contract, associations, Software Vendor, Service Vendor, Hardware Vendor, Third Party | *(clipped)* | ...-26 | ...27T18:30:39Z | ...02T21:24:33Z | | ...Relationship |
| 83 | Customer Relationship Management | crm | crm | Strategy used to manage and analyze customer interactions and data throughout the customer lifecycle, with the goal of improving customer service relationships and assisting in customer retention and driving sales growth Keyword: Retain, Rewards Offers, Cross Sell | 2 | 2018-10-10 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Sales & Relationship |
| 84 | Lead Management | lead_management | lead-management | Manage the process of identifying and evaluating prospects to develop qualified leads to whom offers may be sent. Keywords: Pre-Screen Offer | 2 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Sales & Relationship |
| 85 | Manage Partner Relationships | partner_relationship | partner-relationship | Activites required to manage partner relationships, such as on-boarding partners, maintaining the partner's profile information, and enrolling partners in those services necessary to support interactions between the partner and the firm | 2 | 2019-03-01 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Sales & Relationship |
| 86 | Merchant Loyalty | merchant_loyalty | merchant-loyalty | Processes which help merchants reward their customers, increase revenue and create lasting relationships with repeat shoppers. Merchant Loyalty may include loyalty cards, which are similar to a plastic Gift Card and identifies the card holder as a member in a loyalty program. | 2 | 2019-04-23 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Sales & Relationship |
| 87 | Sales Reporting | sales_reporting | sales-reporting | Returns sales and incentive performance data at branch and employee level | 2 | 2019-03-15 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Sales & Relationship |
| 383 | Third Party Contract Management | third_party_contract_management | 3rdparty-contracts | Manage relationship with third party vendors, partners, investors, dealers and merchants. Includes managing issuer and acquirer agreements with payment networks such as Visa, MasterCard, Discover, and American Express. Maintain channel relationships with those who participate in the sales process. Keywords: Pricing tiers, Profit Sharing, Cost Sharing, Interchange, contract, associations, Software Vendor, Service Vendor, Hardware Vendor, Third Party, MAKE AGREEMENTS | 2 | 2018-11-26 | 2025-09-04T17:12:30Z | 2026-05-29T19:58:01Z | | Sales & Relationship |
| 282 | Eligibility Assessment | eligibility_assessment | eligibility-assessment | The right of a customer to hold or enroll in a Product (e.g., Financial Products, Relationship/Experience Products, Financial Service Product, Product Due Diligence - to determine whether a customer is eligible for a particular product or service, Digital Credit Line Exchange) or a benefit/offer thereof | 2 | 2023-05-11 | 2023-05-11T11:25:51Z | 2026-05-29T19:58:01Z | | Sales & Relationship |
| 56 | Acquisitions Marketing | acquisitions_marketing | acquisitions-marketing | Execution of marketing campaigns to acquire new customers Keywords: Rewards Offers, Partner Offers, Rate Sale | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 57 | Advertising / Media / Social Networking | advertising_media_social_networking | advertising-media | Building our brand, reputation and product awareness through communications via a variety of media and channels. | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 58 | Brand Management | brand_management | brand-management | Defining and influencing the perception of the company and its products, developing that perception via a variety of communications methods and reinforcing it in the way products and services are delivered to customers. | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 59 | Campaign Management | campaign_management | campaign-management | Assess the coverage and impact of internal/ customer campaigns and redirect campaign development and execution activity accordingly Keywords: Analytics, Strategy | 3 | | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 60 | Competitive Intelligence | competitive_intelligence | competitive-intelligence | Evaluation of the awareness, performance, and satisfaction of customers with our products/services as compared to the offerings of our competitors. | 3 | 2018-12-10 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 61 | Marketing Strategy | marketing_strategy | marketing-strategy | Determining the markets & customer segments in which to compete, and defining the products/services and methods to be employed to successfully compete in those markets. | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 62 | Offer Management | offer_management | offer-management | Orchestrate the processing of an offer for a new customer or an existing customer. The offer process is defined primarily by the nature of the product or service being considered, but can include actions such as document checks, collateral allocation, credit assessments, underwriting decisions, regulatory and procedural checks, eligibility checks, the use of internal and external specialist services (such as evaluations and legal advice). Management of rewards offer eligibility rules, including opt-in or opt-out would be included here, but not support of the process to enroll. | 3 | | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 63 | Portfolio Marketing | portfolio_marketing | portfolio-marketing | Execution of marketing campaigns to improve account penetration and profitability with our existing customer base Keywords: Proactive Credit Line Increase (PCLI), Access Checks, Balance Transfer, Loan on Line, Slice, Promo, Rewards, Spend and Get | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 64 | Product Management | product_management | product-management | Management of the product portfolio and product life cycle from concept through retirement. | 3 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Marketing |
| 243 | Catalog Management | catalog_management | catalog-management | Activities required to allow the bank's clients to manage catalogs of products and services offered to their consumers. Includes enabling clients to create and update their inventory of products and services (i.e. "their catalog") and make the catalog information available to their customers. May include services that allow clients to manage their inventory of catalog items by region, store, etc.. Keywords: SKU-level inventory, Merchant Catalog, Rewards Catalog | 3 | 2023-02-24 | 2023-02-24T09:37:46Z | 2026-05-29T19:58:01Z | | Marketing |
| 342 | Manage Rated Offerings | manage_rated_offerings | manage-rated-offerings | Management of an inventory of offerings such as dining locations or vacation packages, for example, for use in loyalty or marketing activities. For example, the bank may gather curated reviews of restaurants (e.g. from Zagat) and manage the list of restaurants to be included/reviewed by criteria such as price range, type of cuisine, etc. But this can go much further than restaurants to include resorts, sightseeing tours and activities, cruises, hotels, etc. Key words: Infatuation, Zagat, Ratings. | 3 | 2025-03-11 | 2025-03-11T22:18:55Z | 2026-05-29T19:58:01Z | | Marketing |
| 78 | Asset Valuation | asset_valuation | asset-valuation | Provides services for the valuation of loans and the assets used to collateralize them. | 4 | 2018-12-11 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Risk |
| 79 | Credit Risk Decisioning | credit_decision | credit-decision | Execution of credit risk models to determine a customer's credit worthiness. | 4 | 2019-03-08 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Risk |
| 80 | Credit Risk Profile | credit_profile | credit-profile | Provides services for analyzing customer creditworthiness and managing exposure. A credit profile consists of assembled and generated data required to make a credit decision regarding a customer. This includes customer stated income, inferred or derived income, credit bureau data, credit scores, and the products and lines that a customer has and contrasting to what they have used, in order to determine their creditworthiness and to assist in making credit decisions Keywords: Credit Reporting Agency, Credit Bureau (Experian, Equifax, TransUnion, Innovis, FICO), Business Bureau (Dunn & Bradstreet, Equifax, Experian, Paynet) | 4 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Risk |
| 81 | Credit Risk Strategy | credit_risk | credit-risk | Activities to develop, maintain and test a credit risk strategy across a product credit life cycle, based on our appetite for risk. Includes scoring and decision model development, behavior analytics, customer treatment optimization, and a reporting and analysis feedback loop. Keywords: Pricing, Re-pricing, Penalty Pricing, Line Management, Credit Line Decrease (CLD), Credit Line Increase (CLI), Exposure Management, Credit Reporting Agency, Credit Bureau (Experian, Equifax, TransUnion, Innovis, FICO), Business Bureau (Dunn & Bradstreet, Equifax, Experian, Paynet) | 4 | 2018-11-26 | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Risk |
| 36 | Authentication | authentication | authentication | Assuring that all account access and transaction activity is restricted to the customer or a duly authorized representative. Includes procedures to facilitate the implementation of identification and authentication controls such as CVV (Card Verification Value), CVV2, CVC (Card Verification Code), chip, RFID, multi-factor authentication (MFA), etc.. For a full breakdown of authentication processes, refer to NIST at: https://gtpc-archer.jpmchase.net/archer/apps/ArcherApp/Home.aspx#record/67/7/208533 Keywords: Chip | 5 | | 2020-04-27T18:30:39Z | 2026-05-29T19:58:01Z | d607893 | Fraud |
| 37 | Fraud Detection | fraud_detection | detection | Update and use measures to detect suspicious/potential fraudulent activity or illegal actions targeting the bank, its customers, its partners, or government agencies. This function includes activities that identify fraud that has happened or is | 5 | | 2020-04-*(clipped)* | 2026-05-*(clipped)* | d607893 | Fraud |

*(the Business Subdomains table continues below the bottom of taxonomy-list3.png — row 37's description and all subsequent rows are not captured)*

---

## Gaps in this set

- **Taxonomy Framework — this is the biggest hole in the whole capture set.** §1–§4 are missing entirely, and the capture dies three rows into the first property table of §5.1.1 (`dcterms:created`). Everything after that — the remaining required concept properties, all optional/relational/mapping properties, and the whole of §5.2 `skos:ConceptScheme` — is uncaptured. The framework's normative content is therefore mostly absent; treat section 1 as an excerpt, not a specification.
- **Taxonomy Information** — *Customer Offering Products* and *Business Domains* tabs appear complete. **Business Subdomains is heavily truncated**: the header row is scrolled off the top, the first visible row is clipped mid-cell, and the table ends at row 37 (Fraud Detection) with an unknown number of rows below. Column labels for that tab are *inferred* from the sibling tab — flagged inline.

---

## Transcription conventions

- Verbatim. Source typos, odd capitalisation and inconsistent section numbering are preserved, not corrected.
- Confluence property tables are rendered as Markdown tables; Turtle / JSON-LD / SHACL / SQL as fenced code blocks with original indentation.
- Rendered diagrams are described in a single italic `*Figure:` line capturing box and arrow labels.
- Overlaps between consecutive screenshots are de-duplicated; where the capture skipped a band, an italic `*(gap …)*` marker names what is missing.
- Sources that are not Confluence pages are labelled as such in their heading.
