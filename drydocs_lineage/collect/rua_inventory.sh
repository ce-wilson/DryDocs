#!/bin/sh
# =============================================================================
# rua_inventory.sh  —  Run-As-User inventory collector
#
# Copy this single file (plus rua_inventory.conf) to a RHEL VSI server and run
# it AS the service / run-as user you want to inventory. It is READ-ONLY: it
# never modifies anything outside its own output directory.
#
# Captures, for the run-as user:
#   * identity   : user, uid, primary/secondary groups, login shell
#   * server     : hostname, OS, kernel, capture timestamp (UTC)
#   * home       : $HOME (resolved real path)
#   * profiles   : .profile / .kshrc / .bash_profile / ... (metadata + a copy)
#   * directories: the user's directory tree under $HOME (+ extra SCAN_ROOTS),
#                  filtered by an ignore list, with owner/group/perms/size/mtime
#   * (optional) : a `find -user` ownership sweep across the local filesystem
#
# Output is a self-describing bundle (meta.txt + *.tsv + profile copies) plus a
# .tar.gz for easy scp back. A lineage extractor can ingest the bundle later
# (drydocs_lineage/extractors/rua_inventory.py, future: server -> node context,
# user -> ProcessNode.run_as, dirs/profiles -> DataAssetNode).
# Re-homed from depgraph@feat/controlm-lineage collect/ (ADR 0002-C §4);
# COLLECTOR_VERSION is the bundle schema stamp — kept identical so bundles
# captured by either copy stay ingestible.
#
# POSIX sh; ksh-compatible. Uses GNU find/stat (standard on RHEL).
#
# Usage:
#   ./rua_inventory.sh [-c config] [-o outdir] [-u user] [-h]
#     -c  config file              (default: ./rua_inventory.conf, else built-ins)
#     -o  output directory parent  (default: current directory)
#     -u  target user to inventory (default: the user running this script)
#     -h  help
# =============================================================================

set -u
COLLECTOR_VERSION="rua-inventory/v1"

# ----------------------------------------------------------------------------- defaults (overridable by config)
SCAN_ROOTS=""            # extra roots beyond $HOME (space-separated); $HOME always included
MAX_DEPTH=4              # directory walk depth (0 = unlimited)
OWNERSHIP_SWEEP="no"     # yes = run the heavy `find / -user <user>` sweep
FOLLOW_SYMLINKS="no"     # yes = follow symlinks during the walk
COPY_PROFILES="yes"      # yes = copy profile files into the bundle
IGNORE_PATTERNS=""       # newline-separated globs, matched against full paths

# profile files we look for in $HOME
PROFILE_CANDIDATES=".profile .profile.local .kshrc .kshrc.local .bash_profile .bashrc .bash_login .login .cshrc .tcshrc .env .environ .netrc.meta"

# ----------------------------------------------------------------------------- helpers
die() { echo "rua_inventory: $*" >&2; exit 1; }
log() { echo "[rua] $*" >&2; }

usage() {
    sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
    exit "${1:-0}"
}

# resolve a user's home directory portably
home_of() {
    _u=$1
    if command -v getent >/dev/null 2>&1; then
        _h=$(getent passwd "$_u" 2>/dev/null | cut -d: -f6)
        [ -n "${_h:-}" ] && { echo "$_h"; return 0; }
    fi
    # fallback: $HOME when inventorying the current user
    if [ "$_u" = "$(id -un 2>/dev/null)" ] && [ -n "${HOME:-}" ] && [ -d "$HOME" ]; then
        echo "$HOME"; return 0
    fi
    # last resort: tilde expansion via eval
    eval _h=~"$_u" 2>/dev/null
    [ -n "${_h:-}" ] && [ -d "$_h" ] && { echo "$_h"; return 0; }
    return 1
}

login_shell_of() {
    _u=$1
    if command -v getent >/dev/null 2>&1; then
        getent passwd "$_u" 2>/dev/null | cut -d: -f7
    fi
}

# true (0) if $1 matches any ignore glob
should_ignore() {
    _p=$1
    [ -z "$IGNORE_PATTERNS" ] && return 1
    _oifs=$IFS
    IFS='
'
    for _pat in $IGNORE_PATTERNS; do
        [ -z "$_pat" ] && continue
        # a trailing-/* pattern (e.g. */logs/*) should also drop the directory
        # NODE itself (~/logs), not just its contents — test the stripped form too
        _bare=${_pat%/\*}
        # shellcheck disable=SC2254  # intentional glob match
        case "$_p" in
            $_pat|$_bare) IFS=$_oifs; return 0 ;;
        esac
    done
    IFS=$_oifs
    return 1
}

# ----------------------------------------------------------------------------- args
CONFIG="./rua_inventory.conf"
OUT_PARENT="."
TARGET_USER=""
while getopts "c:o:u:h" opt 2>/dev/null; do
    case "$opt" in
        c) CONFIG=$OPTARG ;;
        o) OUT_PARENT=$OPTARG ;;
        u) TARGET_USER=$OPTARG ;;
        h) usage 0 ;;
        *) usage 2 ;;
    esac
done

# ----------------------------------------------------------------------------- load config
if [ -f "$CONFIG" ]; then
    log "using config: $CONFIG"
    # parse: KEY=value settings, and repeated IGNORE=<glob> lines
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ''|\#*) continue ;;
        esac
        key=${line%%=*}
        val=${line#*=}
        # trim surrounding whitespace from key
        key=$(printf '%s' "$key" | tr -d '[:space:]')
        case "$key" in
            SCAN_ROOTS)      SCAN_ROOTS=$val ;;
            MAX_DEPTH)       MAX_DEPTH=$val ;;
            OWNERSHIP_SWEEP) OWNERSHIP_SWEEP=$val ;;
            FOLLOW_SYMLINKS) FOLLOW_SYMLINKS=$val ;;
            COPY_PROFILES)   COPY_PROFILES=$val ;;
            IGNORE)          IGNORE_PATTERNS="$IGNORE_PATTERNS
$val" ;;
            *) : ;;  # unknown key: ignore
        esac
    done < "$CONFIG"
else
    log "config not found ($CONFIG) — using built-in defaults + minimal ignore list"
    IGNORE_PATTERNS='/tmp/*
/var/tmp/*
/proc/*
/sys/*
/dev/*
*/.cache/*
*/logs/*
*/log/*
*/tmp/*'
fi

# ----------------------------------------------------------------------------- identity / server facts
RUN_BY=$(id -un 2>/dev/null || whoami 2>/dev/null || echo "${LOGNAME:-${USER:-unknown}}")
[ -n "$TARGET_USER" ] || TARGET_USER=$RUN_BY

HOME_DIR=$(home_of "$TARGET_USER") || die "cannot resolve home for user '$TARGET_USER'"
LOGIN_SHELL=$(login_shell_of "$TARGET_USER")
REAL_HOME=$(cd "$HOME_DIR" 2>/dev/null && pwd -P || echo "$HOME_DIR")

UID_VAL=$(id -u "$TARGET_USER" 2>/dev/null || echo "")
GROUPS_VAL=$(id -Gn "$TARGET_USER" 2>/dev/null || echo "")
PRIMARY_GROUP=$(id -gn "$TARGET_USER" 2>/dev/null || echo "")

HOSTNAME_VAL=$(hostname 2>/dev/null || uname -n 2>/dev/null || echo "unknown")
FQDN_VAL=$(hostname -f 2>/dev/null || echo "$HOSTNAME_VAL")
OS_VAL=$(uname -s 2>/dev/null)
KERNEL_VAL=$(uname -r 2>/dev/null)
OS_PRETTY=$( (. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-}") || echo "")
NOW_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
NOW_TAG=$(date -u +%Y%m%dT%H%M%SZ)

if [ "$RUN_BY" != "$TARGET_USER" ]; then
    log "note: running as '$RUN_BY' but inventorying '$TARGET_USER' — some paths may be unreadable"
fi

# ----------------------------------------------------------------------------- output bundle
SAFE_HOST=$(printf '%s' "$HOSTNAME_VAL" | tr -c 'A-Za-z0-9._-' '_')
SAFE_USER=$(printf '%s' "$TARGET_USER" | tr -c 'A-Za-z0-9._-' '_')
BUNDLE="${OUT_PARENT%/}/rua_${SAFE_HOST}_${SAFE_USER}_${NOW_TAG}"
mkdir -p "$BUNDLE" || die "cannot create output dir: $BUNDLE"
mkdir -p "$BUNDLE/profiles"
DIRS_TSV="$BUNDLE/directories.tsv"
PROF_TSV="$BUNDLE/profiles.tsv"
META="$BUNDLE/meta.txt"
SWEEP_TSV="$BUNDLE/ownership_dirs.tsv"
log "writing bundle: $BUNDLE"

# ----------------------------------------------------------------------------- meta.txt
{
    echo "schema=$COLLECTOR_VERSION"
    echo "collected_at=$NOW_UTC"
    echo "collected_by=$RUN_BY"
    echo "user=$TARGET_USER"
    echo "uid=$UID_VAL"
    echo "primary_group=$PRIMARY_GROUP"
    echo "groups=$GROUPS_VAL"
    echo "login_shell=$LOGIN_SHELL"
    echo "home=$HOME_DIR"
    echo "home_real=$REAL_HOME"
    echo "hostname=$HOSTNAME_VAL"
    echo "fqdn=$FQDN_VAL"
    echo "os=$OS_VAL"
    echo "os_pretty=$OS_PRETTY"
    echo "kernel=$KERNEL_VAL"
    echo "scan_roots=$REAL_HOME $SCAN_ROOTS"
    echo "max_depth=$MAX_DEPTH"
    echo "ownership_sweep=$OWNERSHIP_SWEEP"
    echo "config=$CONFIG"
} > "$META"

# ----------------------------------------------------------------------------- profiles
printf 'name\tpath\texists\tsize\tmtime\tperms\towner\n' > "$PROF_TSV"
PROFILE_FOUND=""
for cand in $PROFILE_CANDIDATES; do
    f="$REAL_HOME/$cand"
    if [ -f "$f" ]; then
        meta_line=$(find "$f" -maxdepth 0 -printf '%s\t%TY-%Tm-%Td %TH:%TM\t%m\t%u\n' 2>/dev/null)
        printf '%s\t%s\tyes\t%s\n' "$cand" "$f" "$meta_line" >> "$PROF_TSV"
        PROFILE_FOUND="$PROFILE_FOUND $cand"
        if [ "$COPY_PROFILES" = "yes" ]; then
            cp -p "$f" "$BUNDLE/profiles/$cand" 2>/dev/null \
                || cp "$f" "$BUNDLE/profiles/$cand" 2>/dev/null \
                || log "could not copy $f"
        fi
    fi
done
echo "profile_files=$(echo $PROFILE_FOUND | tr ' ' ';')" >> "$META"

# ----------------------------------------------------------------------------- directory walk
printf 'path\ttype\towner\tgroup\tperms\tsize\tmtime\n' > "$DIRS_TSV"

find_flags=""
[ "$FOLLOW_SYMLINKS" = "yes" ] && find_flags="-L"
depth_flag=""
[ "${MAX_DEPTH:-0}" != "0" ] && depth_flag="-maxdepth $MAX_DEPTH"

scan_count=0
ignored_count=0
for root in $REAL_HOME $SCAN_ROOTS; do
    [ -d "$root" ] || { log "scan root not a directory, skipping: $root"; continue; }
    # one pass with GNU -printf; filter ignores in the read loop
    # shellcheck disable=SC2086  # depth_flag/find_flags are intentional word-split
    find $find_flags "$root" $depth_flag -type d \
        -printf '%p\t%y\t%u\t%g\t%m\t%s\t%TY-%Tm-%Td %TH:%TM\n' 2>/dev/null \
    | while IFS= read -r rec; do
        path=${rec%%	*}
        if should_ignore "$path"; then
            ignored_count=$((ignored_count + 1))
            continue
        fi
        printf '%s\n' "$rec" >> "$DIRS_TSV"
    done
done
scan_count=$(( $(wc -l < "$DIRS_TSV") - 1 ))
echo "directories_captured=$scan_count" >> "$META"

# ----------------------------------------------------------------------------- optional ownership sweep
if [ "$OWNERSHIP_SWEEP" = "yes" ]; then
    log "ownership sweep (find / -xdev -user $TARGET_USER) — this can take a while..."
    printf 'path\ttype\tperms\tsize\tmtime\n' > "$SWEEP_TSV"
    find / -xdev -user "$TARGET_USER" \( -type d -o -type f \) \
        -printf '%p\t%y\t%m\t%s\t%TY-%Tm-%Td %TH:%TM\n' 2>/dev/null \
    | while IFS= read -r rec; do
        path=${rec%%	*}
        should_ignore "$path" && continue
        printf '%s\n' "$rec" >> "$SWEEP_TSV"
    done
    sweep_count=$(( $(wc -l < "$SWEEP_TSV") - 1 ))
    echo "ownership_objects=$sweep_count" >> "$META"
fi

# ----------------------------------------------------------------------------- provenance: keep the effective config
[ -f "$CONFIG" ] && cp "$CONFIG" "$BUNDLE/rua_inventory.conf.used" 2>/dev/null

# ----------------------------------------------------------------------------- package
TARBALL="${BUNDLE}.tar.gz"
if command -v tar >/dev/null 2>&1; then
    ( cd "$(dirname "$BUNDLE")" && tar czf "$(basename "$TARBALL")" "$(basename "$BUNDLE")" ) \
        && log "packaged: $TARBALL"
fi

# ----------------------------------------------------------------------------- summary
echo "" >&2
echo "================ rua_inventory complete ================" >&2
echo "  user        : $TARGET_USER (uid $UID_VAL) on $HOSTNAME_VAL" >&2
echo "  home        : $REAL_HOME" >&2
echo "  profiles    :${PROFILE_FOUND:- (none found)}" >&2
echo "  directories : $scan_count captured" >&2
echo "  bundle      : $BUNDLE" >&2
[ -f "$TARBALL" ] && echo "  tarball     : $TARBALL" >&2
echo "  scp back    : scp '$TARBALL' you@workstation:~/inventory/" >&2
echo "========================================================" >&2
