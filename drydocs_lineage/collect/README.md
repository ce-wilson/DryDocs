# Run-As-User inventory collector

A single, dependency-free shell script you copy to a RHEL VSI server and run
**as the service / run-as user** you want to inventory. It captures who the user
is, the server, and the user's filesystem footprint (home, profiles, directory
tree) into a portable bundle you scp back and later ingest into the DryDocs
lineage graph (re-homed from depgraph@feat/controlm-lineage, ADR 0002-C §4).

It is **read-only** — it never changes anything outside its own output folder.

## When to use this

You're building an ETL inventory by Control-M folder. The `controlm_jobs` CSV
export gives you each job's `run_as` user + `node_target` (see
`drydocs_lineage.extractors.controlm_inventory`), but not what that user
actually *owns* on the box — its `$HOME`, the `.profile` that sets
`PATH`/sources env, and its working directories. This collector fills that in,
per server, per run-as user.

## Files

| File | Role |
|------|------|
| `rua_inventory.sh`   | the collector (POSIX `sh`; runs under `ksh` on RHEL) |
| `rua_inventory.conf` | settings + the ignore list (tmp / system / logs / caches) |

## Prerequisites

- RHEL (or any Linux with GNU `find`/`stat` — standard on RHEL).
- Run **as the user you want to inventory** (so its files are readable). To
  inventory another user you generally need to `sudo -iu <user>` first, or run
  the script as root with `-u <user>`.
- No packages to install; no network needed.

## Run it

```sh
# 1) copy both files to the server (any writable dir)
scp rua_inventory.sh rua_inventory.conf  you@vsi-host:/tmp/inv/

# 2) on the server, as the run-as user:
cd /tmp/inv
sh ./rua_inventory.sh                 # uses ./rua_inventory.conf, output in .
#   or:
sh ./rua_inventory.sh -c myteam.conf -o /var/tmp/inv   # custom config + outdir
sh ./rua_inventory.sh -u svc.hldm     # inventory another user (needs perms/root)

# 3) bring the bundle back
scp 'you@vsi-host:/tmp/inv/rua_<host>_<user>_<ts>.tar.gz'  ./
```

### Options

| Flag | Meaning | Default |
|------|---------|---------|
| `-c` | config file | `./rua_inventory.conf` (built-in defaults if absent) |
| `-o` | parent dir for the output bundle | current directory |
| `-u` | user to inventory | the user running the script |
| `-h` | help | |

## Configuration (`rua_inventory.conf`)

```ini
SCAN_ROOTS=/opt/app /data/landing   # extra roots beyond $HOME (space-separated)
MAX_DEPTH=4                         # directory-walk depth; 0 = unlimited
FOLLOW_SYMLINKS=no
COPY_PROFILES=yes
OWNERSHIP_SWEEP=no                  # yes = heavy `find / -xdev -user <user>` sweep

IGNORE=*/logs/*                     # one glob per line; matched on the FULL path
IGNORE=/tmp/*                       # a trailing /* pattern also drops the dir node
IGNORE=*/.cache/*                   #   itself (so */logs/* drops ~/logs and below)
```

Ignore globs use shell `case` semantics: `*` matches any run of characters
(including `/`), `?` one character.

## What you get (the bundle)

```
rua_<host>_<user>_<ts>/
  meta.txt                 # key=value: user, uid, groups, shell, home, server,
                           #   os/kernel, scan roots, profile_files, counts
  profiles/                # copies of .profile, .kshrc, .bash_profile, ...
  profiles.tsv             # name, path, size, mtime, perms, owner
  directories.tsv          # path, type, owner, group, perms, size, mtime
  ownership_dirs.tsv       # (only if OWNERSHIP_SWEEP=yes)
  rua_inventory.conf.used  # the exact config used (provenance)
rua_<host>_<user>_<ts>.tar.gz
```

All record files are tab-separated with a header row — the same machine-first
shape the lineage component already ingests (see the CSV-driven
`controlm_inventory` extractor).

## Where bundles live (G19 — the landing zone)

**Bundles NEVER enter the repo tree.** They hold real hostnames, uids, home
paths, and profile/script copies (Internal-Confidential), so they land
out-of-tree — the same idiom as the run logs (`~/logs/DryDocs`):

```
DRYDOCS_DATA_ROOT            env override; default ~/data/DryDocs
  rua/incoming/              carried-back rua_*.tar.gz bundles, as collected
  rua/extracted/<bundle>/    one directory per unpacked bundle
```

Resolution lives in ONE shared helper — `drydocs_core/data_root.py`
(`rua_incoming_dir()` / `rua_extracted_dir(bundle)`); the G20 extractor reads
from there. The source is registered as `rua-inventory` in
`config/source-registry.yaml` (`confirmed: false` until the G22 gate — nothing
writes the graph before it), and `tests/unit/test_data_root.py` sweeps the
repo tree to enforce that only the pointer, never a bundle, is committed.
Transport from the server stays per the internal-local hand-carry note.

## How it connects back to the lineage graph

The bundle is the **server-side half** of the inventory. A future lineage
extractor (`drydocs_lineage/extractors/rua_inventory.py`) will read a bundle
and add:

- the server as context (node/agent placement is the Epic P hosts-topology
  work — `node_target` is polymorphic, per gate controlm-hosts-topology),
- the run-as user as the bridge to `ProcessNode.run_as` (tying these files to the
  Control-M jobs that run as that user),
- `$HOME` and captured directories as `DataAssetNode`s the user owns,
- `.profile`/`.kshrc` as script artifacts (they set `PATH` and source other
  scripts — a real dependency edge worth following).

That keeps the lineage source explicit: **server → run-as user → path → file →
dependency**, exactly the shape the graph needs.

## Safety notes

- Read-only; writes only under the `-o` directory.
- Permission-denied paths during the walk are silently skipped (normal when not
  root). Run as the target user (or root with `-u`) for a complete picture.
- `OWNERSHIP_SWEEP=yes` walks the whole local filesystem (`-xdev`, one fs) and
  can take minutes on large hosts — leave it off unless you need it.
