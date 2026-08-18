"""Doctor transcript scan: tool usage, skills, hooks, denials. Read-only.

Environment tooling, not DryDocs domain code — it reads this machine's Claude Code
transcripts (``~/.claude/projects/*/*.jsonl``) over the 50 most recently modified
sessions and reports aggregates: MCP calls by server, Skill dispatches, slash
commands, hook timings and timeouts, and tool denials.

Useful for answering "what is this setup actually doing" — which permissions prompt
most often, whether a hook is slow or timing out, which skills ever fire. Pairs with
the ``fewer-permission-prompts`` skill, which acts on the denial counts.

It emits counts and tool names only, never transcript content. Nothing is written.

Usage::

    poetry run python scripts/doctor_scan.py
"""

import glob
import json
import os
from collections import Counter, defaultdict
from datetime import UTC, datetime

H = os.path.expanduser("~")
files = glob.glob(os.path.join(H, ".claude", "projects", "*", "*.jsonl"))
files.sort(key=os.path.getmtime, reverse=True)
files = files[:50]
if not files:
    print("NO TRANSCRIPTS")
    raise SystemExit

oldest = datetime.fromtimestamp(min(os.path.getmtime(f) for f in files), tz=UTC)
newest = datetime.fromtimestamp(max(os.path.getmtime(f) for f in files), tz=UTC)

mcp_calls = Counter()  # server -> count
tool_calls = Counter()  # non-mcp tool name -> count
skill_calls = Counter()  # skill name via Skill tool
slash_cmds = Counter()
hook_stats = defaultdict(list)  # (hookName, hookEvent) -> [durationMs]
hook_timeouts = Counter()
denials = Counter()  # (kind, pattern) -> count
tooluse_index = {}  # id -> (name, first token of command)


def bash_key(inp):
    cmd = (inp or {}).get("command", "")
    parts = cmd.strip().split()
    if not parts:
        return "Bash(<empty>)"
    key = parts[0]
    if len(parts) > 1 and parts[0] in (
        "git",
        "gh",
        "npm",
        "poetry",
        "docker",
        "python",
        "cargo",
        "go",
    ):
        key += " " + parts[1]
    return key[:60]


for fp in files:
    try:
        with open(fp, encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                t = e.get("type")
                if t == "assistant":
                    for c in (e.get("message") or {}).get("content") or []:
                        if isinstance(c, dict) and c.get("type") == "tool_use":
                            name = c.get("name", "")
                            tooluse_index[c.get("id")] = (
                                name,
                                bash_key(c.get("input")) if name == "Bash" else name,
                            )
                            if name.startswith("mcp__"):
                                seg = name.split("__")
                                mcp_calls[seg[1] if len(seg) > 1 else name] += 1
                            elif name == "Skill":
                                skill_calls[(c.get("input") or {}).get("skill", "?")] += 1
                            else:
                                tool_calls[name] += 1
                elif t == "attachment":
                    a = e.get("attachment") or {}
                    at = a.get("type", "")
                    if at.startswith("hook_"):
                        key = (a.get("hookName"), a.get("hookEvent"))
                        if at == "hook_cancelled" and a.get("timedOut"):
                            hook_timeouts[key] += 1
                        d = a.get("durationMs")
                        if isinstance(d, int | float):
                            hook_stats[key].append(d)
                elif t == "user":
                    kind = e.get("toolDenialKind")
                    content = e.get("message", {}).get("content")
                    if kind and kind not in ("interrupted", "cancelled"):
                        tuid = None
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, dict) and c.get("type") == "tool_result":
                                    tuid = c.get("tool_use_id")
                        name, pat = tooluse_index.get(tuid, ("?", "?"))
                        denials[(kind, name if name != "Bash" else "Bash: " + pat)] += 1
                    if isinstance(content, str) and "<command-name>" in content:
                        try:
                            cmd = content.split("<command-name>")[1].split("</command-name>")[0]
                            slash_cmds[cmd.strip()] += 1
                        except Exception:
                            pass
    except Exception as ex:
        print("SKIP", os.path.basename(fp), ex)

print(f"WINDOW: {len(files)} sessions, {oldest:%Y-%m-%d} .. {newest:%Y-%m-%d}")
print("\n== MCP calls by server ==")
for k, v in mcp_calls.most_common():
    print(f"  {k}: {v}")
print("\n== Skill tool dispatches ==")
for k, v in skill_calls.most_common():
    print(f"  {k}: {v}")
print("\n== Slash commands ==")
for k, v in slash_cmds.most_common(15):
    print(f"  {k}: {v}")
print("\n== Hooks ==")
if not hook_stats and not hook_timeouts:
    print("  (no hook runs recorded)")
for key, ds in hook_stats.items():
    ds.sort()
    print(
        f"  {key}: n={len(ds)} typ={ds[len(ds) // 2]}ms max={ds[-1]}ms "
        f"timeouts={hook_timeouts.get(key, 0)}"
    )
print("\n== Denials (toolDenialKind, excluding aborts) ==")
if not denials:
    print("  (none)")
for (kind, pat), v in denials.most_common(20):
    print(f"  [{kind}] {pat}: {v}")
