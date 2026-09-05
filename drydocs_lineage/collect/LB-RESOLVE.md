# Load-balancer name resolution collector (`lb_resolve.sh`)

A single, dependency-free shell script you copy to a Linux host on the network
the schedule runs on. It asks DNS what a list of Control-M node names actually
answers with, and writes the answers down verbatim. It is **read-only** — it
issues queries and writes nothing outside its own output directory.

> **This file, and not `README.md`.** That README is titled "Run-As-User
> inventory collector" and is rua-specific throughout. Backlog **G132 clause
> (e)** owns the decision of whether it becomes a directory index for a
> multi-collector `collect/`, so this collector documents itself beside it
> rather than pre-empting that call. Whoever takes G132 now has three
> collectors' worth of reason to make the index.

## What it is for

A Control-M job is scheduled against a node name, and that name is often a
load-balancer alias rather than a machine. The signed server-location tiers
(gate `server-location-ontology`, 12/12, 2026-08-19) join a name to an
inventory `:Server` only when the strings meet — **T1** exact, **T2** the
short-name/FQDN rule — so an alias meets neither, is correctly reported
UNMATCHED, and every job behind it stays unplaceable on the map. **T3
`dns-resolved`** is the tier the gate declared for precisely this case and left
unbuilt. This collector supplies its evidence.

## Which names to feed it — the coverage report already says

The input is the **UNMATCHED rows of the Z3 query
`infra.app-job-host-locations.v1`**: exactly the hosts T1 and T2 could not
place. Nothing anywhere in this chain guesses whether a name "looks like" a
load balancer. A naming convention read off a hostname is an unsigned rule, and
it is the same class of guess the T2 ambiguity guard exists to refuse — so the
classification happens **by outcome**, in the extractor, from what DNS said.

## Run it

```sh
# 1) copy the script to the host (any writable dir)
scp lb_resolve.sh  you@host:/tmp/lb/

# 2) put one node name per line in a list (# comments and blanks are ignored)
#    — these are the UNMATCHED job hosts from the Z3 query

# 3) on the host:
cd /tmp/lb
sh ./lb_resolve.sh -i hosts.txt
sh ./lb_resolve.sh -i hosts.txt -o /var/tmp/lb   # custom output parent
sh ./lb_resolve.sh -i hosts.txt -s 10.0.0.53     # query a specific resolver

# 4) bring the bundle back
scp 'you@host:/tmp/lb/lb_<host>_<ts>.tar.gz'  ./
```

| Flag | Meaning | Default |
|------|---------|---------|
| `-i` | input list, one node name per line | **required** |
| `-o` | parent dir for the output bundle | current directory |
| `-s` | resolver to query | the host's own configured resolver |
| `-h` | help | |

**There is no `.conf` sibling, on purpose.** Everything this collector would
configure is either a CLI argument or an Internal value (`CLAUDE.md` §3), and a
committed conf template with an endpoint-shaped key is an invitation to fill it
in and commit it back.

## What you get (the bundle)

```
lb_<host>_<ts>/
  meta.txt              # schema, collected_at (UTC), collector_host,
                        #   lookup_source, resolver, queried count
  queried.tsv           # query_name, transcript_file, exit_code
  nslookup/<name>.txt   # ONE FILE PER NAME, the tool's stdout VERBATIM,
                        #   with a leading `; query: <name>` line
lb_<host>_<ts>.tar.gz
```

`COLLECTOR_VERSION` (`lb-resolve/v1`) is stamped into `meta.txt` as `schema=`,
the same discipline `rua_inventory.sh` follows and for the same reason: two
copies of this script will exist — one on the server, one here — before they
converge, and a transcript read months later has to say which one wrote it.

## Shell collects, Python parses

No field extraction happens in the script. The answer files hold the tool's
output whole, which is what lets the parser be tested against a canned
transcript with no DNS anywhere near it, and what lets a real transcript be
re-read from scratch if the parser changes. `tests/unit/test_lineage_lb_resolution.py`
asserts this — the script may not contain `awk`, `grep -o` or `cut -d`.

## The other half

`drydocs_lineage/extractors/lb_resolution.py` reads a bundle and matches the
answers against the ingested server list, classifying each queried name by what
came back:

| Outcome | Meaning |
|---|---|
| `matched` | DNS answered, and at least one name it gave is an inventory server. One alias fronting three servers produces three records — the fan-out the gate anticipated. |
| `unmatched` | DNS answered and nothing it named is in the inventory. A real gap, and the names are **listed**, not just counted. |
| `unresolved` | NXDOMAIN, or the resolver could not answer. |
| `unreadable` | A transcript the parser could not make sense of — counted, because a parser that silently drops what it does not understand reports a clean run over a format change. |

Matched records carry `nodeid`, `server`, `match_tier: 'dns-resolved'` and a
`match_evidence` string — the `RESOLVES_TO_SERVER` shape
`drydocs/loaders/server_resolution.py` already promises T3 will arrive in, so a
loader consumes the evidence file unchanged. **This chain writes no edges.**
Every graph write goes through the gated shapes, and that is a separate act.

## Where bundles live

Bundles hold real hostnames and resolver addresses, so they never enter the
repo tree — the same rule as the rua bundles (`README.md`, "Where bundles
live"): out-of-tree under `DRYDOCS_DATA_ROOT`, hand-carried back per the
internal-local note. The only committed transcript is the synthetic fixture at
`tests/fixtures/lineage/lb_resolve/`, whose names are invented.
