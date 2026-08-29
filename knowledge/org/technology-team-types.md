# Agile Product Architecture, Team Types, and Interaction Models

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