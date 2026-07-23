# Local Neo4j Login — Setup Overview & Troubleshooting

**Classification:** Internal (operational metadata — local host-port mapping; no
credentials, password lives in local `.env`). Committed at the 2026-07-11 documentation
tech-debt review (D2): this was untracked tribal knowledge, invisible to other machines.
Raw console evidence from the same troubleshooting: `internal-local/` (gitignored).

## Overview

We run Neo4j locally in Docker for testing. The container exposes its internal
ports (`7474` HTTP/Browser, `7687` Bolt) to the host, but Docker may remap
them to different host ports depending on how the container was started
(e.g. if the defaults were already taken). Always check the actual mapping
with `docker port <container_id>` rather than assuming the Neo4j defaults.

## Current local mapping (as of 2026-07-23 — container `neo4jtest`)

| Service              | Container port | Host port |
|----------------------|-----------------|-----------|
| HTTP (Neo4j Browser)  | 7474            | 7474      |
| Bolt (driver/queries) | 7687            | 7687      |

- **Browser UI:** http://localhost:7474/browser/
- **Bolt connection string:** bolt://localhost:7687
- **Login:** username `neo4j`, password — see local secrets/`.env` (not committed here)

> History: the earlier container `neo4j-drydocs-ee` sat on remapped host ports
> 7476/7689 (the 2026-07-02 troubleshooting below is from that era). On 2026-07-23
> its data was migrated into the named volume `neo4j-testdata` and the canonical
> container `neo4jtest` (config/dev-environment.yaml) was recreated on the default
> ports. The old container is kept stopped as a rollback copy.

> These host ports can change if the container is recreated. Re-check with
> `docker port <container_id>` if login stops working.

## Steps to diagnose a local connection issue

1. **Confirm the container is running:**
   ```
   docker ps
   ```
   Note the container ID.

2. **Check the actual port mapping** (don't assume 7474/7687 on the host):
   ```
   docker port <container_id>
   ```
   Example output:
   ```
   7474/tcp -> 0.0.0.0:7476
   7687/tcp -> 0.0.0.0:7689
   ```

3. **Open the Neo4j Browser** at the host port mapped to container port `7474`:
   ```
   http://localhost:<mapped-7474-port>/browser/
   ```

4. **In the Browser's connect screen**, use the host port mapped to container
   port `7687` for the Bolt connection URL:
   ```
   bolt://localhost:<mapped-7687-port>
   ```
   Login with `neo4j` / `<password>`.

5. **If login still fails**, check the container logs for real errors:
   ```
   docker logs <container_id>
   ```
   A clean startup log looks like:
   ```
   INFO  Bolt enabled on 0.0.0.0:7687.
   INFO  Bolt (Routing) enabled on 0.0.0.0:7688.
   INFO  HTTP enabled on 0.0.0.0:7474.
   INFO  Remote interface available at http://localhost:7474/
   INFO  Started.
   ```
   No errors here means the server itself is healthy — a login failure at
   that point is almost always either (a) wrong host port, or (b)
   wrong/stale password.

6. **If the password doesn't match**, check how it was set at container boot:
   ```
   docker inspect <container_id> --format '{{.Config.Env}}'
   ```
   Look for `NEO4J_AUTH=neo4j/<password>`.

## What went wrong last time (2026-07-02)

- Tried browsing to `http://localhost:7689/browser/` — this was the **Bolt**
  host port, not the HTTP/Browser port, so it returned raw JSON
  (`{"auth_config":{"oidc_providers":[]}}`) instead of the Browser UI.
- Container logs showed a clean startup with no errors, which correctly
  pointed at a port-mismatch rather than an auth/server problem.
- Running `docker port <container_id>` revealed the real mapping
  (7476 → HTTP, 7689 → Bolt), and using `http://localhost:7476/browser/`
  with Bolt URL `bolt://localhost:7689` resolved the issue.
