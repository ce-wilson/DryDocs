# W3C ORG — the Organization ontology

**IRI:** `http://www.w3.org/ns/org#`. Models org structure: `org:Organization`,
`org:OrganizationalUnit`, `org:FormalOrganization`, `org:Membership` (n-ary role-holder node),
`org:Role`.

## DryDocs usage
- **SEAL:** `Application` has `Membership` → `Role`, held by `Employee`.
- **Catalog / PAT (LOB→Product→Team):** `CatalogLOB` (OrgUnit), `BusinessSegment`
  (FormalOrganization), `DevTeam` (OrgUnit), team-role memberships.
- Use the **n-ary `Membership` pattern** for any timed role assignment (carries
  `valid_from`/`valid_to`) — do not collapse it to a direct edge.

See the SEAL + Catalog blocks in `relationship_vocabulary.yaml`. The org taxonomy
(LOB→Product→Team) is also the **lowest precedence authority** in `config/precedence.yaml`.
