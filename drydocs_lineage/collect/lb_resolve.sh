#!/bin/sh
# =============================================================================
# lb_resolve.sh  —  load-balancer name resolution collector (backlog Z4)
#
# Copy this single file to a Linux host that sits on the network the schedule
# runs on, give it a list of Control-M node names, and run it. It is READ-ONLY:
# it issues DNS queries and writes nothing outside its own output directory.
#
# WHAT IT IS FOR. A Control-M job is scheduled against a node name, and that
# name is often a load-balancer alias rather than a machine. The signed
# server-location tiers resolve a name to an inventory :Server exactly when the
# strings meet — T1 exact, T2 the short-name/FQDN rule — and a load-balancer
# alias meets neither, so it is reported UNMATCHED and the job cannot be placed
# on the map at all. This collector supplies the third tier's evidence: what
# the alias actually answers with. The extractor
# (drydocs_lineage/extractors/lb_resolution.py) turns that into
# match_tier 'dns-resolved' records against the ingested server list.
#
# WHICH NAMES TO FEED IT — the coverage report already says. The input list is
# the UNMATCHED rows of the Z3 query infra.app-job-host-locations.v1: the hosts
# T1 and T2 could not place, which is precisely the candidate set. Nothing here
# guesses whether a name "looks like" a load balancer; the classification is by
# OUTCOME, in the extractor, from what DNS answered. A naming convention read
# off a hostname is exactly the kind of invention the tiers were signed to
# avoid.
#
# SHELL COLLECTS, PYTHON PARSES (the rua_inventory.sh precedent, ADR 0002-C §4).
# Every nslookup answer is written to its own file VERBATIM — no field
# extraction here. That is what lets the parser be tested against a canned
# transcript with no DNS anywhere near it, and what lets a transcript captured
# on a company host be re-read later, whole, if the parser changes.
#
# NOTHING CONFIGURABLE LIVES IN A COMMITTED FILE. There is no .conf sibling on
# purpose: everything this collector would configure — which resolver, which
# names — is either a CLI argument or an Internal value (CLAUDE.md section 3),
# and a committed conf template with an endpoint-shaped key invites someone to
# fill it in and commit it back.
#
# POSIX sh; ksh-compatible. Needs nslookup (bind-utils on RHEL); host(1) is
# used as a fallback ONLY to record that nslookup was absent, never to produce
# a differently-shaped answer.
#
# Usage:
#   ./lb_resolve.sh -i hosts.txt [-o outdir] [-s resolver] [-h]
#     -i  input file: one node name per line; blank lines and # comments
#         ignored                                              (required)
#     -o  output directory parent   (default: current directory)
#     -s  resolver to query         (default: the host's own configured one)
#     -h  help
# =============================================================================

set -u
COLLECTOR_VERSION="lb-resolve/v1"

INPUT=""
OUTDIR="."
RESOLVER=""

die() { echo "lb_resolve: $*" >&2; exit 1; }
log() { echo "[lb] $*" >&2; }

usage() {
    sed -n '2,50p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
}

while getopts ":i:o:s:h" opt; do
    case "$opt" in
        i) INPUT="$OPTARG" ;;
        o) OUTDIR="$OPTARG" ;;
        s) RESOLVER="$OPTARG" ;;
        h) usage ;;
        \?) die "unknown option -$OPTARG (try -h)" ;;
        :) die "option -$OPTARG needs a value" ;;
    esac
done

[ -n "$INPUT" ] || die "no input list: pass -i <file> with one node name per line"
[ -r "$INPUT" ] || die "cannot read input list: $INPUT"

# The query tool, recorded rather than assumed: a bundle parsed months later
# has to say what produced it.
if command -v nslookup >/dev/null 2>&1; then
    LOOKUP_SOURCE="nslookup"
elif command -v host >/dev/null 2>&1; then
    LOOKUP_SOURCE="host"
else
    die "neither nslookup nor host is available — install bind-utils"
fi

HOSTNAME_VALUE="$(hostname 2>/dev/null || echo unknown)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BUNDLE="lb_${HOSTNAME_VALUE}_${STAMP}"
BUNDLE_DIR="${OUTDIR}/${BUNDLE}"

mkdir -p "${BUNDLE_DIR}/nslookup" || die "cannot create ${BUNDLE_DIR}"

# One file per queried name, named by a SAFE form of the name. The name itself
# travels inside the file's own first line and in queried.tsv, so the sanitizing
# can never lose it.
safe_name() {
    echo "$1" | tr -c 'A-Za-z0-9._-' '_'
}

QUERIED=0
printf 'query_name\ttranscript_file\texit_code\n' > "${BUNDLE_DIR}/queried.tsv"

while IFS= read -r raw || [ -n "$raw" ]; do
    name="$(echo "$raw" | sed 's/#.*//' | tr -d '[:space:]')"
    [ -n "$name" ] || continue
    file="$(safe_name "$name").txt"
    target="${BUNDLE_DIR}/nslookup/${file}"

    # The queried name goes in as a comment line so a transcript file is
    # self-identifying even when read on its own.
    printf '; query: %s\n' "$name" > "$target"
    if [ "$LOOKUP_SOURCE" = "nslookup" ]; then
        if [ -n "$RESOLVER" ]; then
            nslookup "$name" "$RESOLVER" >> "$target" 2>&1
        else
            nslookup "$name" >> "$target" 2>&1
        fi
    else
        host "$name" ${RESOLVER:+"$RESOLVER"} >> "$target" 2>&1
    fi
    rc=$?
    printf '%s\t%s\t%s\n' "$name" "nslookup/${file}" "$rc" >> "${BUNDLE_DIR}/queried.tsv"
    QUERIED=$((QUERIED + 1))
done < "$INPUT"

{
    printf 'schema=%s\n' "$COLLECTOR_VERSION"
    printf 'collected_at=%s\n' "$STAMP"
    printf 'collector_host=%s\n' "$HOSTNAME_VALUE"
    printf 'lookup_source=%s\n' "$LOOKUP_SOURCE"
    printf 'resolver=%s\n' "${RESOLVER:-host-default}"
    printf 'queried=%s\n' "$QUERIED"
} > "${BUNDLE_DIR}/meta.txt"

log "queried ${QUERIED} name(s) with ${LOOKUP_SOURCE} -> ${BUNDLE_DIR}"

if command -v tar >/dev/null 2>&1; then
    (cd "$OUTDIR" && tar -czf "${BUNDLE}.tar.gz" "$BUNDLE") \
        && log "bundle: ${OUTDIR}/${BUNDLE}.tar.gz"
fi
