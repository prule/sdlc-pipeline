#!/usr/bin/env python3
"""
session_report.py — turn a Claude Code session log (.jsonl) into a beautiful,
self-contained HTML report focused on pipeline efficiency.

Usage:
    python3 session_report.py <session.jsonl> [-o report.html] [--out-dir DIR]
                              [--context-dirs domain,standards] [--compact] [--open]
                              [--summary]

The report shows:
  * a summary of the session (duration, tokens, agent runs, errors, issues caught)
  * a Gantt-style timeline of every agent/subagent run — who ran, when, how long
    (use --compact to collapse idle gaps so short runs stay visible)
  * a subagent value / efficiency table with auto-generated insights, including
    the model and effort each agent ran, as recorded by Claude Code
  * a Review-gate value panel — which review agents actually caught something
  * an Errors & friction panel — failed commands, rejected tool calls, failed agents
  * a readable, filterable chronological activity feed

Background ("run_in_background") agents launch with an instant stub result; their
real duration and output arrive later in a <task-notification>. This script
correlates the two so async agents are timed and reported correctly.

--summary prints one JSON object instead of the status lines: the session id,
report path, Claude Code version, and the orchestrator's and each agent type's
model and effort (plus runs). build-use-case copies it into the retrospective.

No third-party dependencies — standard library only. Output is one HTML file.
"""

from __future__ import annotations

import argparse
import bisect
import html
import json
import posixpath
import re
import shlex
import sys
import webbrowser
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# subagents that act as review / verification gates
GATE_AGENTS = {"spec-reviewer", "senior-dev", "qa", "code-review", "reviewer"}


def is_gate(subagent_type: str) -> bool:
    """Plugin agents are namespaced (`sdlc-pipeline:qa`); match on the short name."""
    return str(subagent_type).rsplit(":", 1)[-1] in GATE_AGENTS


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #

def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_events(path):
    events = []
    with open(path, "r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                sys.stderr.write(f"warning: skipping malformed line {i}\n")
    return events


def blocks(msg):
    if not isinstance(msg, dict):
        return
    content = msg.get("content")
    if isinstance(content, list):
        for b in content:
            if isinstance(b, dict):
                yield b
    elif isinstance(content, str) and content:
        yield {"type": "text", "text": content}


def text_of(block):
    if not isinstance(block, dict):
        return str(block)
    if isinstance(block.get("text"), str):
        return block["text"]
    c = block.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "".join(x.get("text", "") for x in c if isinstance(x, dict))
    return ""


def msg_text(msg):
    return "".join(
        b.get("text", "") for b in blocks(msg) if b.get("type") == "text"
    )


# --------------------------------------------------------------------------- #
# Task-notification (async agent completion) parsing
# --------------------------------------------------------------------------- #

_TAG = lambda name, s: (re.search(rf"<{name}>(.*?)</{name}>", s, re.S) or [None, None])[1]


def parse_notification(text):
    if "<task-notification>" not in text:
        return None
    result = re.search(r"<result>(.*?)</result>", text, re.S)
    return {
        "task_id": _TAG("task-id", text),
        "tool_use_id": _TAG("tool-use-id", text),
        "status": (_TAG("status", text) or "").strip(),
        "summary": (_TAG("summary", text) or "").strip(),
        "result": result.group(1).strip() if result else "",
    }


def parse_handback(ev):
    """A subagent's final report delivered as a peer message (the SubagentHandback
    path). Its task-notification then carries only a pointer ("delivered to you as
    a message"), so the verdict text lives here. Returns (agent_id, report) or None."""
    origin = ev.get("origin") or {}
    body = origin.get("body") or ""
    if origin.get("kind") != "peer" or "[Subagent hand-back]" not in body:
        return None
    report = body.split("The report follows:", 1)[-1]
    report = "\n".join(l[2:] if l.startswith("  ") else l for l in report.splitlines())
    return origin.get("from") or origin.get("senderTaskId"), report.strip()


# --------------------------------------------------------------------------- #
# Review-verdict classification
# --------------------------------------------------------------------------- #

def classify_review(text):
    """Return (verdict, caught?, issue_count, snippet) for a review agent result.

    Keys off *formal* verdict tokens and uppercase severity labels rather than
    loose substrings, so "failure path" / "critically" (adverbs) don't
    false-positive, and "no CRITICAL issues" is treated as clean.
    """
    t = text or ""
    tl = t.lower()

    def issue_count():
        # allow one qualifier word: "3 blocking findings", "2 real bugs"
        nums = [int(m) for m in re.findall(
            r"(?<![§.#\w])(\d{1,2})\s+(?:[a-z-]+\s+)?(?:issue|finding|defect|bug|blocker|problem|violation)s?\b", tl)]
        explicit = max(nums) if nums else 0
        sev = t.count("❌") + len(re.findall(r"\bCRITICAL\b", t))
        return min(99, max(explicit, sev))

    def snippet_near(*keys):
        for k in keys:
            i = tl.find(k.lower())
            if i != -1:
                return re.sub(r"\s+", " ", t[i:i + 240]).strip()
        return re.sub(r"\s+", " ", t[:200]).strip()

    # 1) formal "REQUEST CHANGES" gate verdict — unambiguous
    if re.search(r"request[ _-]?changes", tl):
        return "REQUEST CHANGES", True, issue_count(), snippet_near("request change")
    if re.search(r"\bNOT READY\b", t):
        return "NOT READY", True, issue_count(), snippet_near("NOT READY")

    # 1b) approved, but the gate found/fixed something on the way (QA logging a
    #     defect, senior-dev fixing in place) — still a catch, not a rubber stamp
    fixed = re.search(r"\b(?:i fixed|fixes (?:to|applied)|fixed the|fixes i applied)\b"
                      r"(?![^a-z]*(?:none|nothing|n/a)\b)", tl)   # not "Fixes applied: none"
    found = re.search(r"^#+\s*defects? found|(?<!no )\bdefect found\b|\bstandards? violation\b", tl, re.M)
    if fixed or found:
        label = "FIXED IN PLACE" if fixed else "DEFECT LOGGED"
        return label, True, max(1, issue_count()), snippet_near(
            "fixed", "fixes", "defect found", "violation")

    # 2) hard catch signals: uppercase severity labels, ❌, or "critical <noun>".
    #    Guarded so "no/0/zero critical" isn't counted as a catch.
    only_clean_critical = bool(re.search(r"\b(?:no|0|zero)\s+critical", tl)) \
        and not re.search(r"\b[1-9]\d*\s+critical", tl)
    has_critical = bool(re.search(r"\bCRITICAL\b", t)) and not only_clean_critical
    if (has_critical or "❌" in t or re.search(r"\bFAIL(?:ED)?\b", t)
            or re.search(r"(?<!no )(?<!0 )(?<!zero )critical (?:defect|issue|bug|finding|blocker)", tl)):
        return "ISSUES FOUND", True, issue_count(), snippet_near("CRITICAL", "❌", "FAIL", "defect")

    # 3) explicit approval / pass
    if re.search(r"\bapprove", tl) or "lgtm" in tl or "✅" in t or re.search(r"\bpass(?:ed)?\b", tl):
        return "APPROVED / PASS", False, 0, snippet_near("approve", "pass", "lgtm")

    return "—", False, issue_count(), re.sub(r"\s+", " ", t[:200]).strip()


REJECT_MARKERS = ("doesn't want to proceed", "tool use was rejected", "user rejected")


def classify_error(name, text):
    tl = (text or "").lower()
    if any(m in tl for m in REJECT_MARKERS):
        return "rejected"        # you declined the tool call — friction, not a bug
    return "error"               # command / tool actually failed


# --------------------------------------------------------------------------- #
# Shared aggregation helpers (reused by main log and each subagent transcript)
# --------------------------------------------------------------------------- #

READ_TOOLS = {"Read"}
WRITE_TOOLS = {"Write"}
EDIT_TOOLS = {"Edit", "MultiEdit", "NotebookEdit"}


# --------------------------------------------------------------------------- #
# Shell file access — agents read and write files with cat, sed, grep and
# redirects as often as with the file tools. Best effort: common forms only.
# --------------------------------------------------------------------------- #

SHELL_READERS = {"cat", "less", "more", "wc", "head", "tail", "sed", "grep", "egrep", "rg"}
# options that take a value, per command (so `head -n 5` skips the 5, but `sed -n`
# and `grep -n` don't swallow the script or pattern)
_TAKES_VALUE = {
    "head": {"-n", "-c"}, "tail": {"-n", "-c"},
    "sed": {"-e", "-f"},
    "grep": {"-e", "-f", "-A", "-B", "-C", "-m", "--max-count"},
    "rg": {"-e", "-f", "-A", "-B", "-C", "-m", "--max-count", "-g", "--glob", "-t", "--type"},
}
_TAKES_VALUE["egrep"] = _TAKES_VALUE["grep"]
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n.*?\n[ \t]*\2[ \t]*(?=\n|$)", re.S)


def _file_args(args, pattern_first, takes_value=()):
    """Non-flag arguments, skipping option values and (for sed/grep) the script
    or pattern unless it was given with -e/-f."""
    out, skip, explicit = [], False, False
    for a in args:
        if skip:
            skip = False
            continue
        if a.startswith("-") and a != "-":
            if a in ("-e", "-f", "--regexp", "--file"):
                explicit = True
            if a in takes_value:
                skip = True
            continue
        out.append(a)
    if pattern_first and not explicit and out:
        out = out[1:]
    return out


def _simple_command(toks):
    ops, args, i = [], [], 0
    while i < len(toks):
        t = toks[i]
        if t[0] in "<>&" and set(t) <= set("<>&|"):
            target = toks[i + 1] if i + 1 < len(toks) else ""
            if "&" in t and ">" in t and t != "&>" and t != "&>>":
                i += 2                      # >&2, 2>&1: a file descriptor, not a file
                continue
            if target:
                ops.append(("write" if ">" in t else "read", target))
            i += 2
            continue
        if t.isdigit() and i + 1 < len(toks) and toks[i + 1].startswith(">"):
            i += 1                          # the 2 in 2>file
            continue
        args.append(t)
        i += 1
    while args and (re.match(r"^\w+=", args[0]) or args[0] in ("sudo", "command", "exec", "time")):
        args = args[1:]
    if not args:
        return ops
    name, rest = posixpath.basename(args[0]), args[1:]
    if name == "sed":
        in_place = any(a.startswith("-i") or a == "--in-place" for a in rest)
        files = _file_args([a for a in rest if not a.startswith("-i")], True, _TAKES_VALUE["sed"])
        ops += [("write" if in_place else "read", f) for f in files]
    elif name in ("grep", "egrep", "rg"):
        ops += [("read", f) for f in _file_args(rest, True, _TAKES_VALUE[name])]
    elif name in SHELL_READERS:
        ops += [("read", f) for f in _file_args(rest, False, _TAKES_VALUE.get(name, ()))]
    elif name == "tee":
        ops += [("write", f) for f in _file_args(rest, pattern_first=False)]
    elif name in ("cp", "mv"):
        files = _file_args(rest, pattern_first=False)
        if len(files) >= 2:
            ops += [("read", f) for f in files[:-1]] + [("write", files[-1])]
    return ops


def _pathlike(p):
    return (bool(p) and not p.startswith(("-", "$", "/dev/")) and not p.endswith("/") and not re.search(r"[*?\[\]{}$`]", p)
            and not p.isdigit() and ("/" in p or "." in p.lstrip(".")))


def shell_file_ops(command, cwd=None):
    """[(op, path)] for the files a shell command reads or writes with common file
    commands (cat, head, tail, sed, grep, redirects, tee, cp, mv). Relative paths
    are resolved against cwd; a `cd` inside the command is ignored."""
    ops = []
    for line in _HEREDOC.sub(r"\3", command or "").splitlines():
        try:
            lex = shlex.shlex(line, posix=True, punctuation_chars=True)
            lex.whitespace_split = True
            toks = list(lex)
        except ValueError:
            continue
        cmd = []
        for tok in toks + [";"]:
            if set(tok) <= set(";&|()") and tok not in ("&>", "&>>"):
                ops += _simple_command(cmd)
                cmd = []
            else:
                cmd.append(tok)
    out = []
    for op, p in ops:
        if not _pathlike(p):
            continue
        if cwd and not p.startswith(("/", "~")):
            p = posixpath.normpath(posixpath.join(cwd, p))
        out.append((op, p))
    return out


INTERNAL_PATH = re.compile(r"/\.claude/|/tool-results/|/subagents/|/scratchpad/|^/private/tmp/claude-"
                           r"|^/tmp/claude-")


def is_internal(path):
    """Claude Code's own files: transcripts, tool results, the scratchpad."""
    return bool(INTERNAL_PATH.search(path or ""))


def file_ops_from_tools(tools):
    files = defaultdict(lambda: {"read": 0, "write": 0, "edit": 0, "shell": 0,
                                 "first": None, "last": None})

    def note(path, op, ts, shell=False):
        if not path or is_internal(path):
            return
        rec = files[path]
        rec[op] += 1
        rec["shell"] += int(shell)
        if ts:
            rec["first"] = ts if rec["first"] is None else min(rec["first"], ts)
            rec["last"] = ts if rec["last"] is None else max(rec["last"], ts)

    for t in tools:
        inp = t["input"] if isinstance(t["input"], dict) else {}
        ts = t.get("start")
        if t["name"] == "Bash":
            for op, path in shell_file_ops(inp.get("command"), t.get("cwd")):
                note(path, op, ts, shell=True)
            continue
        path = inp.get("file_path") or inp.get("notebook_path")
        if t["name"] in READ_TOOLS:
            note(path, "read", ts)
        elif t["name"] in WRITE_TOOLS:
            note(path, "write", ts)
        elif t["name"] in EDIT_TOOLS:
            note(path, "edit", ts)
    return dict(files)


def tool_stats_from_tools(tools):
    stats = defaultdict(lambda: {"count": 0, "time": 0.0, "err": 0})
    for t in tools:
        s = stats[t["name"]]
        s["count"] += 1
        s["time"] += t.get("duration") or 0
        if t.get("error"):
            s["err"] += 1
    return dict(stats)


def merge_file_ops(dicts):
    out = defaultdict(lambda: {"read": 0, "write": 0, "edit": 0, "shell": 0,
                               "first": None, "last": None})
    for d in dicts:
        for path, r in d.items():
            o = out[path]
            for k in ("read", "write", "edit", "shell"):
                o[k] += r.get(k, 0)
            for key in ("first", "last"):
                if r[key]:
                    o[key] = r[key] if o[key] is None else (
                        min(o[key], r[key]) if key == "first" else max(o[key], r[key]))
    return dict(out)


def merge_tool_stats(dicts):
    out = defaultdict(lambda: {"count": 0, "time": 0.0, "err": 0})
    for d in dicts:
        for name, s in d.items():
            o = out[name]
            o["count"] += s["count"]; o["time"] += s["time"]; o["err"] += s["err"]
    return dict(out)


def correlate_tools(events):
    """Pair tool_use with tool_result within one transcript; return a tools list
    plus token totals, time span, and the first real user prompt."""
    uses, results = {}, {}
    tokens = defaultdict(int)
    first = last = first_prompt = None
    for ev in events:
        ts = parse_ts(ev.get("timestamp"))
        if ts:
            first = ts if first is None else min(first, ts)
            last = ts if last is None else max(last, ts)
        m = ev.get("message")
        if ev.get("type") == "user" and isinstance(m, dict):
            for b in blocks(m):
                if b.get("type") == "tool_result":
                    results[b.get("tool_use_id")] = {
                        "ts": ts, "is_error": bool(b.get("is_error"))}
            if first_prompt is None:
                t = msg_text(m).strip()
                if t:
                    first_prompt = t
        elif ev.get("type") == "assistant" and isinstance(m, dict):
            u = m.get("usage") or {}
            for k in ("input_tokens", "output_tokens",
                      "cache_creation_input_tokens", "cache_read_input_tokens"):
                tokens[k] += u.get(k, 0) or 0
            for b in blocks(m):
                if b.get("type") == "tool_use":
                    uses[b["id"]] = {"name": b.get("name", "?"),
                                     "input": b.get("input") or {}, "ts": ts,
                                     "cwd": ev.get("cwd")}
    tools = []
    for tid, u in uses.items():
        r = results.get(tid)
        dur = (r["ts"] - u["ts"]).total_seconds() if (r and r["ts"] and u["ts"]) else None
        tools.append({"id": tid, "name": u["name"], "input": u["input"],
                      "start": u["ts"], "duration": dur, "cwd": u["cwd"],
                      "error": r["is_error"] if r else None})
    return tools, dict(tokens), first, last, first_prompt


def transcript_stats(events):
    """The work recorded in a transcript, or in one run's slice of it."""
    tools, tokens, first, last, prompt = correlate_tools(events)
    dur = (last - first).total_seconds() if first and last else None
    return {
        "tools": tools,
        "file_ops": file_ops_from_tools(tools),
        "tool_stats": tool_stats_from_tools(tools),
        "tool_calls": len(tools), "tokens": tokens,
        "duration": dur, "prompt": prompt,
        "errors": sum(1 for t in tools if t["error"]),
        "ctx": context_signals(events),
        "model": primary_model(events),
        "effort": recorded_effort(events),
    }


def load_subagents(session_path):
    """Parse every subagents/agent-*.jsonl beside the main log, with the
    agent-*.meta.json Claude Code writes beside it (toolUseId, agentType…) when
    there is one. Returns {agentId: stats} keyed by the transcript's agentId."""
    sub_dir = Path(session_path).with_suffix("") / "subagents"
    if not sub_dir.is_dir():
        return {}
    out = {}
    for f in sorted(sub_dir.glob("agent-*.jsonl")):
        aid = f.stem[len("agent-"):]
        events = load_events(f)
        if not events:
            continue
        try:
            meta = json.loads(f.with_suffix(".meta.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = {}
        out[aid] = {**transcript_stats(events), "agent_id": aid,
                    "events": events, "meta": meta if isinstance(meta, dict) else {}}
    return out


def primary_model(events):
    """The model that produced the most assistant messages in a transcript."""
    c = Counter()
    for ev in events:
        m = ev.get("message")
        if isinstance(m, dict) and m.get("role") == "assistant":
            mdl = m.get("model")
            if mdl and mdl != "<synthetic>":
                c[mdl] += 1
    return c.most_common(1)[0][0] if c else None


def recorded_effort(events):
    """The effort level(s) Claude Code recorded on a transcript's assistant
    messages: `perTurnEffort`, else `effort`. These fields are undocumented, so
    nothing is inferred when they're absent — the answer is then "unknown"."""
    seen = set()
    for ev in events:
        m = ev.get("message")
        if ev.get("type") != "assistant" or not isinstance(m, dict):
            continue
        if m.get("model") == "<synthetic>":
            continue
        e = ev.get("perTurnEffort") or ev.get("effort")
        if e:
            seen.add(str(e))
    return ", ".join(sorted(seen)) if seen else "unknown"


# --------------------------------------------------------------------------- #
# Context ingestion — did agents read/use the curated context docs
# (domain/ and standards/ by default; see --context-dirs)?
# --------------------------------------------------------------------------- #

CONTEXT_DIRS = ("domain", "standards")


def context_re(dirs):
    alts = "|".join(re.escape(d.strip("/")) for d in dirs)
    return re.compile(rf"(?:{alts})/[A-Za-z0-9_.-]+\.md")


CONTEXT_RE = context_re(CONTEXT_DIRS)
WRITE_ALL = WRITE_TOOLS | EDIT_TOOLS


def context_signals(events):
    """From one transcript, return context-doc reads (with timing relative to
    the first write), and references to those docs in the agent's own text."""
    reads = []          # (relpath, ts)
    refs = Counter()    # relpath -> mentions in assistant text
    first_write = None
    for ev in events:
        ts = parse_ts(ev.get("timestamp"))
        m = ev.get("message")
        if not isinstance(m, dict):
            continue
        for b in blocks(m):
            bt = b.get("type")
            if bt == "tool_use":
                name = b.get("name")
                inp = b.get("input") or {}
                if name in WRITE_ALL and ts:
                    first_write = ts if first_write is None else min(first_write, ts)
                if name == "Read":
                    mt = CONTEXT_RE.search(str(inp.get("file_path", "")))
                    if mt:
                        reads.append((mt.group(0), ts))
                elif name == "Bash":
                    for op, path in shell_file_ops(inp.get("command"), ev.get("cwd")):
                        if op == "write" and ts:
                            first_write = ts if first_write is None else min(first_write, ts)
                        mt = CONTEXT_RE.search(path) if op == "read" else None
                        if mt:
                            reads.append((mt.group(0), ts))
            elif bt == "text" and ev.get("type") == "assistant":
                for mt in CONTEXT_RE.findall(b.get("text", "")):
                    refs[mt] += 1
    informed = sum(1 for _, ts in reads
                   if first_write is None or (ts and ts < first_write))
    return {"reads": reads, "refs": dict(refs),
            "first_write": first_write, "informed": informed}


def build_context(data, project_root=None):
    """Aggregate context ingestion across the orchestrator and all subagents."""
    per_file = defaultdict(lambda: {"reads": 0, "informed": 0, "refs": 0,
                                    "readers": set()})
    per_agent = defaultdict(lambda: {"reads": 0, "informed": 0, "refs": 0})
    catches_by_doc = Counter()          # doc -> # gate catches that cite it

    def ingest(cs, agent):
        for relpath, ts in cs["reads"]:
            f = per_file[relpath]
            f["reads"] += 1
            f["readers"].add(agent)
            informed = cs["first_write"] is None or (ts and ts < cs["first_write"])
            if informed:
                f["informed"] += 1
            per_agent[agent]["reads"] += 1
            per_agent[agent]["informed"] += int(bool(informed))
        for relpath, n in cs["refs"].items():
            per_file[relpath]["refs"] += n
            per_agent[agent]["refs"] += n

    if data.get("ctx_main"):
        ingest(data["ctx_main"], "(orchestrator)")
    for a in data["agents"]:
        s = a.get("sub")
        if s and s.get("ctx"):
            ingest(s["ctx"], a["subagent"])
        # attribute reviewer catches to the docs they cite
        if a.get("gate") and a.get("caught") and a.get("result"):
            for doc in set(CONTEXT_RE.findall(a["result"])):
                catches_by_doc[doc] += 1

    # universe of docs + their sizes (to flag never-read and gauge bloat)
    universe = set()
    sizes = {}                          # relpath -> approx tokens (chars / 4)
    root = Path(project_root or Path.cwd())
    for sub in CONTEXT_DIRS:
        d = root / sub
        if d.is_dir():
            for p in d.glob("*.md"):
                rel = f"{sub}/{p.name}"
                universe.add(rel)
                try:
                    sizes[rel] = max(1, len(p.read_text(encoding="utf-8")) // 4)
                except OSError:
                    pass
    never_read = sorted(universe - set(per_file)) if universe else []
    read_never_ref = sorted(f for f, v in per_file.items()
                            if v["reads"] and not v["refs"])

    return {"per_file": dict(per_file), "per_agent": dict(per_agent),
            "catches_by_doc": dict(catches_by_doc), "sizes": sizes,
            "never_read": never_read, "read_never_ref": read_never_ref,
            "universe": bool(universe)}


def _norm_prompt(s):
    return re.sub(r"\s+", " ", s or "").strip()[:120]


RESUME_MARKER = "The coordinator sent a message"


def link_subagents(data, subs):
    """Attach each subagent transcript to the Agent call that started it, then
    split it between that run and every resumed run of the same agent, so each
    run carries its own work. Builds the session-wide file/tool aggregates."""
    notes = data.setdefault("notes", [])
    by_tid = {s["meta"]["toolUseId"]: s for s in subs.values() if s["meta"].get("toolUseId")}
    by_prompt = {_norm_prompt(s["prompt"]): s for s in subs.values()
                 if not s["meta"].get("toolUseId")}
    agents = data["agents"]
    n_prompt = 0
    for a in agents:
        a.update({"sub": None, "linked_by": None, "model": None, "effort": "unknown"})
    for a in agents:
        if a.get("resume"):
            continue
        s = by_tid.get(a["id"])
        if s:
            a["linked_by"] = "id"
        else:
            s = by_prompt.get(_norm_prompt(a["input"].get("prompt")))
            if s:
                a["linked_by"] = "prompt"
                n_prompt += 1
        if not s:
            continue
        runs = sorted([a] + [r for r in agents if r.get("resume") and r.get("parent_id") == a["id"]],
                      key=lambda r: r["start"] or datetime.max.replace(tzinfo=timezone.utc))
        for r in runs[1:]:
            r["linked_by"] = "resume"
        split_runs(runs, s, notes)
    if n_prompt:
        notes.append(f"{n_prompt} run(s) linked by prompt: their transcripts record no "
                     "tool-use id, so two runs that open with the same prompt could be mixed up.")
    data["files_all"] = merge_file_ops(
        [data["files"]] + [s["file_ops"] for s in subs.values()])
    data["tool_stats_all"] = merge_tool_stats(
        [data["tool_stats"]] + [s["tool_stats"] for s in subs.values()])
    data["subagents"] = subs
    data["has_sub"] = True


def split_runs(runs, s, notes):
    """Give each run the slice of transcript s that falls between its start and the
    next run's start. The resume markers in the transcript are only a cross-check:
    their wording is undocumented."""
    name = runs[0]["subagent"]
    whole = {k: v for k, v in s.items() if k not in ("events", "meta")}
    if len(runs) == 1:
        runs[0].update({"sub": whole, "model": s["model"], "effort": s["effort"]})
        return
    starts = [r["start"] for r in runs[1:]]
    if any(st is None for st in starts):
        runs[0].update({"sub": whole, "model": s["model"], "effort": s["effort"]})
        for r in runs[1:]:
            r.update({"model": s["model"], "effort": s["effort"]})
        notes.append(f"{name}: a resumed run has no start time, so all of its work is "
                     "credited to the first run.")
        return
    buckets, i = [[] for _ in runs], 0
    for ev in s["events"]:
        t = parse_ts(ev.get("timestamp"))
        if t:
            i = bisect.bisect_right(starts, t)
        buckets[i].append(ev)
    for r, evs in zip(runs, buckets):
        st = transcript_stats(evs)
        st["prompt"] = st["prompt"] or s["prompt"]
        r.update({"sub": {**st, "agent_id": s["agent_id"]},
                  "model": st["model"] or s["model"],
                  "effort": st["effort"] if st["effort"] != "unknown" else s["effort"]})
    markers = sum(1 for ev in s["events"] if ev.get("type") == "user"
                  and msg_text(ev.get("message")).lstrip().startswith(RESUME_MARKER))
    if markers != len(runs) - 1:
        notes.append(f"{name}: {len(runs) - 1} resumed run(s) but {markers} resume marker(s) "
                     "in its transcript; work is split by the runs' start times.")


# --------------------------------------------------------------------------- #
# Core analysis
# --------------------------------------------------------------------------- #

def analyze(events):
    tool_uses = {}
    tool_results = {}
    notifications = defaultdict(list)     # tool_use_id -> [notification, ...]
    handbacks = defaultdict(list)         # agent_id -> [{"ts", "text"}, ...]
    tool_counter = Counter()
    models = Counter()
    tokens = defaultdict(int)

    timeline = []
    first_ts = last_ts = None
    meta = {}
    versions = []                         # every Claude Code version, in order seen
    waits = []                            # (last event, user prompt): time waiting on the human
    prev_ts = None

    for ev in events:
        ts = parse_ts(ev.get("timestamp"))
        before, prev_ts = prev_ts, (ts or prev_ts)
        if ts:
            first_ts = ts if first_ts is None else min(first_ts, ts)
            last_ts = ts if last_ts is None else max(last_ts, ts)
        for k in ("sessionId", "cwd", "gitBranch", "version"):
            if k in ev and k not in meta:
                meta[k] = ev[k]
        if ev.get("version") and ev["version"] not in versions:
            versions.append(ev["version"])
        if ev.get("type") == "custom-title" and ev.get("customTitle"):
            meta.setdefault("title", ev["customTitle"])

        etype = ev.get("type")
        msg = ev.get("message")

        if etype == "user" and isinstance(msg, dict):
            hb = parse_handback(ev)
            if hb:
                handbacks[hb[0]].append({"ts": ts, "text": hb[1]})
                continue
            raw = msg_text(msg)
            note = parse_notification(raw)
            if note:
                if note["tool_use_id"]:
                    note["ts"] = ts
                    notifications[note["tool_use_id"]].append(note)
                continue

            has_result = False
            for b in blocks(msg):
                if b.get("type") == "tool_result":
                    has_result = True
                    tid = b.get("tool_use_id")
                    if tid:
                        tool_results[tid] = {
                            "ts": ts,
                            "is_error": bool(b.get("is_error")),
                            "text": text_of(b),
                        }
            prompt = raw.strip()
            # skip injected/system-wrapped user content (task-notifications handled,
            # system-reminders, local-command output, etc.)
            if prompt and not has_result and not prompt.startswith("<"):
                timeline.append({"ts": ts, "kind": "user", "text": prompt})
                if before and ts and ts > before:
                    waits.append((before, ts))

        elif etype == "assistant" and isinstance(msg, dict):
            models[msg.get("model", "unknown")] += 1
            usage = msg.get("usage") or {}
            for k in ("input_tokens", "output_tokens",
                      "cache_creation_input_tokens", "cache_read_input_tokens"):
                tokens[k] += usage.get(k, 0) or 0
            for b in blocks(msg):
                bt = b.get("type")
                if bt == "text" and b.get("text", "").strip():
                    timeline.append({"ts": ts, "kind": "assistant",
                                     "text": b["text"].strip()})
                elif bt == "thinking" and b.get("thinking", "").strip():
                    timeline.append({"ts": ts, "kind": "thinking",
                                     "text": b["thinking"].strip()})
                elif bt == "tool_use":
                    tid = b.get("id")
                    name = b.get("name", "?")
                    tool_counter[name] += 1
                    tool_uses[tid] = {"name": name, "input": b.get("input") or {},
                                      "ts": ts, "cwd": ev.get("cwd")}
                    timeline.append({"ts": ts, "kind": "tool", "tool": name,
                                     "input": b.get("input") or {}, "id": tid})

    # ---- correlate uses <-> results / notifications --------------------- #
    tools, agents, errors = [], [], []
    for tid, use in tool_uses.items():
        res = tool_results.get(tid)
        notes = notifications.get(tid) or []
        last_note = notes[-1] if notes else None

        # completion time & result: notification wins over the async stub
        if last_note and last_note.get("ts"):
            end = last_note["ts"]
            result_text = last_note["result"]
            status = last_note["status"]
            is_error = status not in ("completed", "", None)
        elif res:
            end = res["ts"]
            result_text = res["text"]
            is_error = res["is_error"]
            status = "error" if is_error else "completed"
        else:
            end, result_text, is_error, status = None, None, None, "pending"

        dur = (end - use["ts"]).total_seconds() if (end and use["ts"]) else None
        rec = {
            "id": tid, "name": use["name"], "input": use["input"],
            "start": use["ts"], "end": end, "duration": dur,
            "error": is_error, "result": result_text, "status": status,
            "pending": end is None, "cwd": use.get("cwd"),
        }
        tools.append(rec)

        # collect real errors / rejections (skip async launch stubs)
        if res and res["is_error"]:
            errors.append({
                "ts": use["ts"], "tool": use["name"],
                "kind": classify_error(use["name"], res["text"]),
                "input": use["input"], "text": res["text"],
            })

        if use["name"] == "Agent":
            inp = use["input"]
            sub = inp.get("subagent_type", "agent")
            m = re.search(r"agentId:\s*([\w-]+)", (res or {}).get("text") or "")
            agents.append({
                **rec, "subagent": sub, "gate": is_gate(sub),
                "description": inp.get("description", ""),
                "background": bool(inp.get("run_in_background")),
                "agent_id": m.group(1) if m else None, "resume": False,
            })

    # ---- SendMessage to a spawned agent = another run of that agent ------ #
    # (orchestrator correction loops: architect revisions, reviewer re-reviews)
    spawned = {a["agent_id"]: a for a in agents if a["agent_id"]}
    for t in tools:
        if t["name"] != "SendMessage":
            continue
        inp = t["input"] if isinstance(t["input"], dict) else {}
        m = re.search(r'"resumedAgentId"\s*:\s*"([\w-]+)"',
                      (tool_results.get(t["id"]) or {}).get("text") or "")
        target = m.group(1) if m else inp.get("to")
        parent = spawned.get(target)
        if not parent:
            continue          # a message to a peer session, not a subagent run
        desc = inp.get("summary") or truncate(inp.get("message", ""), 80)
        agents.append({
            **t, "input": {"subagent_type": parent["subagent"], "description": desc,
                           "prompt": inp.get("message", "")},
            "subagent": parent["subagent"], "gate": parent["gate"],
            "description": desc, "background": True,
            "agent_id": target, "resume": True, "parent_id": parent["id"],
        })

    # ---- attach each run's hand-back report (the real output) ------------ #
    runs_by_agent = defaultdict(list)
    for a in agents:
        if a["agent_id"]:
            runs_by_agent[a["agent_id"]].append(a)
    for aid, runs in runs_by_agent.items():
        runs.sort(key=lambda r: r["start"] or datetime.max.replace(tzinfo=timezone.utc))
        for i, r in enumerate(runs):
            nxt = runs[i + 1]["start"] if i + 1 < len(runs) else None
            hb = next((h for h in handbacks.get(aid, [])
                       if h["ts"] and r["start"] and h["ts"] >= r["start"]
                       and (nxt is None or h["ts"] < nxt)), None)
            if hb:
                r.update({"result": hb["text"], "end": hb["ts"], "pending": False,
                          "status": "completed", "error": False,
                          "duration": (hb["ts"] - r["start"]).total_seconds()})

    for a in agents:
        a.update({"verdict": None, "verdict_source": None, "caught": None, "issues": None,
                  "snippet": None, "findings": None})
        if a["gate"] and a["result"]:
            found = parse_findings(a["result"])
            if found is not None:
                v = findings_verdict(found)
                n = sum(1 for f in found if f["status"] in ("handed-back", "fixed-in-place"))
                a.update({"verdict": v, "verdict_source": "findings", "findings": found,
                          "caught": v in ("handed-back", "fixed-in-place"), "issues": n,
                          "snippet": first_line(a["result"])})
            else:
                v, c, n, s = classify_review(a["result"])
                a.update({"verdict": v, "verdict_source": "inferred",
                          "caught": c, "issues": n, "snippet": s})

    by_id = {t["id"]: t for t in tools}
    agent_by_id = {a["id"]: a for a in agents}
    for item in timeline:
        if item.get("kind") == "tool":
            t = by_id.get(item.get("id"))
            if t:
                item.update({"duration": t["duration"], "error": t["error"],
                             "result": t["result"], "status": t["status"]})
                a = agent_by_id.get(item["id"])
                if a:
                    item.update({"verdict": a["verdict"], "caught": a["caught"],
                                 "gate": a["gate"], "duration": a["duration"],
                                 "result": a["result"], "error": a["error"],
                                 "agent_view": True, "resume": a["resume"],
                                 "input": a["input"]})

    files = file_ops_from_tools(tools)
    tool_stats = tool_stats_from_tools(tools)

    agents.sort(key=lambda a: a["start"] or datetime.max.replace(tzinfo=timezone.utc))
    timeline.sort(key=lambda x: x["ts"] or datetime.max.replace(tzinfo=timezone.utc))
    errors.sort(key=lambda e: e["ts"] or datetime.max.replace(tzinfo=timezone.utc))

    meta["versions"] = versions
    return {
        "meta": meta, "first_ts": first_ts, "last_ts": last_ts,
        "models": models, "tokens": dict(tokens),
        "main_model": primary_model(events), "main_effort": recorded_effort(events),
        "tool_counter": tool_counter, "tool_stats": dict(tool_stats),
        "tools": tools, "agents": agents, "files": dict(files),
        "ctx_main": context_signals(events),
        "errors": errors, "timeline": timeline, "waits": waits, "notes": [],
    }


# --------------------------------------------------------------------------- #
# Gate findings — the "Run-log findings" block each gate ends its report with:
#   - **Q1** · kind: test-gap · severity: high · rule: `standards/x.md §2`
#     · where: `src/a.ts:10` · status: handed-back (defect for the junior dev)
#     - root cause: ...
#     - recommendation: ...
# --------------------------------------------------------------------------- #

_FINDINGS_HEAD = re.compile(r"^[#*\s]*Run-log findings[*:\s]*$", re.M | re.I)
_FINDING = re.compile(r"^\s*[-*]\s+\*\*([A-Z]+\d+)\*\*\s*(.*)$")
_SUB_BULLET = re.compile(r"^[-*]\s+(root cause|recommendation)\s*:\s*(.*)$", re.I)


def _clean(v):
    v = re.sub(r"\s+", " ", (v or "").replace("`", "")).strip()
    return None if v in ("", "—", "-", "–") else v


def parse_findings(text):
    """The findings in a gate's Run-log findings block: a list of dicts (empty when
    the block says None), or None when the text has no block at all."""
    m = _FINDINGS_HEAD.search(text or "")
    if not m:
        return None
    body = text[m.end():]
    nxt = re.search(r"^#{1,6}\s", body, re.M)
    if nxt:
        body = body[:nxt.start()]
    entries, cur = [], None
    for line in body.splitlines():
        fm = _FINDING.match(line)
        if fm:
            cur = {"id": fm.group(1), "head": fm.group(2), "subs": []}
            entries.append(cur)
            continue
        s = line.strip()
        if cur is None or not s:
            continue
        sm = _SUB_BULLET.match(s)
        if sm:
            cur["subs"].append([sm.group(1).lower().replace(" ", "_"), sm.group(2)])
        elif cur["subs"]:
            cur["subs"][-1][1] += " " + s
        else:
            cur["head"] += " " + s
    out = []
    for e in entries:
        f = {"id": e["id"], "kind": None, "severity": None, "rule": None, "where": None,
             "status": None, "root_cause": None, "recommendation": None}
        for part in e["head"].split("·"):
            k, sep, v = part.partition(":")
            k = k.strip().lower()
            if sep and k in f:
                f[k] = _clean(v)
        for k, v in e["subs"]:
            f[k] = _clean(v)
        f["status"] = re.split(r"[\s(]", f["status"] or "", 1)[0].lower() or "unknown"
        out.append(f)
    return out


def findings_verdict(findings):
    statuses = {f["status"] for f in findings}
    if "handed-back" in statuses:
        return "handed-back"
    if "fixed-in-place" in statuses:
        return "fixed-in-place"
    return "clean"          # nothing found, or a re-check confirming earlier fixes


def first_line(text):
    for line in (text or "").splitlines():
        line = line.strip().strip("#>*_ ").strip()
        if line:
            return truncate(line, 240)
    return ""


REJECTING = {"handed-back", "REQUEST CHANGES", "NOT READY", "ISSUES FOUND"}


def short_name(subagent):
    return str(subagent).rsplit(":", 1)[-1]


def tokens4(raw):
    """Claude's usage keys -> the four counts the report shows."""
    raw = raw or {}
    return {"input": raw.get("input_tokens", 0), "cache_write": raw.get("cache_creation_input_tokens", 0),
            "cache_read": raw.get("cache_read_input_tokens", 0), "output": raw.get("output_tokens", 0)}


def add_tokens(*ts):
    out = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0}
    for t in ts:
        for k in out:
            out[k] += (t or {}).get(k, 0)
    return out


def run_tokens(a):
    return tokens4((a.get("sub") or {}).get("tokens"))


def build_fix_loops(agents):
    """A loop starts at a gate run that handed findings back. The non-gate runs that
    follow are its fixes, as long as each is a resumed run or an agent that already
    ran before the gate; a fresh agent starts the next phase and ends the loop. The
    next run of the same gate re-checks and ends it; a different gate ends it
    without a re-check. A rejection that nothing fixed is not a loop."""
    runs = sorted((a for a in agents if a["start"]), key=lambda a: a["start"])
    loops = []
    for i, a in enumerate(runs):
        if not a["gate"] or a.get("verdict") not in REJECTING:
            continue
        seen = {r["subagent"] for r in runs[:i]}
        fixes, recheck = [], None
        for b in runs[i + 1:]:
            if b["gate"]:
                recheck = b if short_name(b["subagent"]) == short_name(a["subagent"]) else None
                break
            if not b.get("resume") and b["subagent"] not in seen:
                break
            fixes.append(b)
        if not fixes:
            continue
        members = fixes + ([recheck] if recheck else [])
        loops.append({
            "gate": short_name(a["subagent"]), "started_by": a["id"],
            "findings": [f["id"] for f in (a.get("findings") or []) if f["status"] == "handed-back"],
            "fix_runs": [b["id"] for b in fixes],
            "recheck_run": recheck["id"] if recheck else None,
            "start": a["start"], "end": max((b["end"] or b["start"] for b in members), default=a["end"]),
            "duration_s": sum(b["duration"] or 0 for b in members),
            "tool_calls": sum((b.get("sub") or {}).get("tool_calls", 0) for b in members),
            "tokens": add_tokens(*(run_tokens(b) for b in members)),
        })
    return loops


def _union(ivs):
    out = []
    for s, e in sorted(iv for iv in ivs if iv[0] and iv[1] and iv[1] > iv[0]):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def _subtract(ivs, cover):
    out = []
    for s, e in ivs:
        cur = s
        for cs, ce in cover:
            if ce <= cur or cs >= e:
                continue
            if cs > cur:
                out.append([cur, cs])
            cur = max(cur, ce)
        if cur < e:
            out.append([cur, e])
    return out


def _secs(ivs):
    return sum((e - s).total_seconds() for s, e in ivs)


def time_breakdown(data):
    """Wall time split into agents working (parallel runs counted once), waiting on
    the human (questions, and gaps before the user's next prompt while no agent
    ran), and the orchestrator (the rest)."""
    first, last = data["first_ts"], data["last_ts"]
    wall = (last - first).total_seconds() if first and last else 0.0
    agent_iv = _union([(a["start"], a["end"]) for a in data["agents"]])
    asks = [(t["start"], t["end"]) for t in data["tools"] if t["name"] == "AskUserQuestion"]
    human_iv = _subtract(_union(asks + data.get("waits", [])), agent_iv)
    agents_s, human_s = _secs(agent_iv), _secs(human_iv)
    return {"wall_s": round(wall, 1), "agents_s": round(agents_s, 1),
            "human_wait_s": round(human_s, 1),
            "orchestrator_s": round(max(0.0, wall - agents_s - human_s), 1),
            "human_intervals": human_iv}


_UC = re.compile(r"use-cases/(UC-\d+(?:\.\d+)*)")
_CHANGE = re.compile(r"(?:--change[= ]|new change )\s*[\"']?([A-Za-z0-9][\w.-]*)")


def find_ids(data):
    """The use case and OpenSpec change the session worked on, when it names them."""
    texts = [it.get("text", "") for it in data["timeline"] if it["kind"] == "user"]
    texts += [json.dumps(t["input"]) for t in data["tools"] if t["name"] in ("Skill", "Agent")]
    uc = next((m.group(1) for s in texts for m in [_UC.search(s)] if m), None)
    cmds = [t["input"].get("command", "") for t in data["tools"] if t["name"] == "Bash"]
    for s in (data.get("subagents") or {}).values():
        cmds += [t["input"].get("command", "") for t in s["tools"] if t["name"] == "Bash"]
    changes = Counter(m.group(1) for c in cmds for m in _CHANGE.finditer(c or ""))
    return uc, (changes.most_common(1)[0][0] if changes else None)


def relative_files(files, root):
    """Re-key file records by path relative to the project root (outside paths keep
    their full path, with the home folder shortened to ~)."""
    out = {}
    prefix = (root or "").rstrip("/") + "/"
    for path, rec in files.items():
        if root and path.startswith(prefix):
            key = path[len(prefix):]
        else:
            key = re.sub(r"^/(?:Users|home)/[^/]+/", "~/", path)
        out = merge_file_ops([out, {key: rec}]) if key in out else {**out, key: rec}
    return out


def analyze_session(path, project_root=None, no_subagents=False):
    """Everything the report and the summary need, from one session log."""
    events = load_events(path)
    if not events:
        raise ValueError(f"no parseable events in {path}")
    data = analyze(events)
    subs = {} if no_subagents else load_subagents(path)
    if subs:
        link_subagents(data, subs)
    else:
        data.update({"files_all": data["files"], "tool_stats_all": data["tool_stats"],
                     "subagents": {}, "has_sub": False})
    root = data["meta"].get("cwd")
    data["files_all"] = relative_files(data["files_all"], root)
    data["findings"] = [{**f, "gate": short_name(a["subagent"]), "run": a["id"]}
                        for a in data["agents"] for f in (a.get("findings") or [])]
    data["fix_loops"] = build_fix_loops(data["agents"])
    data["time"] = time_breakdown(data)
    data["tokens_total"] = add_tokens(tokens4(data["tokens"]),
                                      *(tokens4(s["tokens"]) for s in data["subagents"].values()))
    data["use_case"], data["change"] = find_ids(data)
    data["ctx"] = build_context(data, project_root=project_root)
    return data


# --------------------------------------------------------------------------- #
# Idle-gap collapse for the --compact Gantt
# --------------------------------------------------------------------------- #

def build_remap(intervals, idle_cap=8.0):
    """Piecewise-linear map real-time -> compressed-seconds, capping idle gaps
    (spans where no agent is running) at idle_cap seconds."""
    pts = sorted({p for iv in intervals for p in iv})
    if len(pts) < 2:
        return (lambda t: 0.0), 1.0
    comp = {pts[0]: 0.0}
    cum = 0.0
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        dt = (b - a).total_seconds()
        active = any(s <= a and e >= b for s, e in intervals)
        if not active and dt > idle_cap:
            dt = idle_cap
        cum += dt
        comp[b] = cum

    def remap(t):
        if t <= pts[0]:
            return 0.0
        if t >= pts[-1]:
            return cum
        i = bisect.bisect_right(pts, t) - 1
        a, b = pts[i], pts[i + 1]
        seg_real = (b - a).total_seconds()
        seg_comp = comp[b] - comp[a]
        frac = 0 if seg_real == 0 else (t - a).total_seconds() / seg_real
        return comp[a] + frac * seg_comp

    return remap, (cum or 1.0)


# --------------------------------------------------------------------------- #
# Formatting
# --------------------------------------------------------------------------- #

def fmt_dur(s):
    if s is None:
        return "—"
    s = max(0, s)
    if s < 1:
        return f"{s*1000:.0f}ms"
    if s < 60:
        return f"{s:.1f}s"
    m, sec = divmod(int(s), 60)
    if m < 60:
        return f"{m}m {sec}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m"


def fmt_ts(dt):
    return dt.strftime("%H:%M:%S") if dt else "—"


def fmt_num(n):
    return f"{n:,}"


def esc(s):
    return html.escape(str(s))


def truncate(s, n=280):
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


PALETTE = ["#6366f1", "#ec4899", "#14b8a6", "#f59e0b", "#8b5cf6", "#ef4444",
           "#10b981", "#3b82f6", "#f97316", "#a855f7", "#06b6d4", "#84cc16"]


def colour_map(names):
    return {n: PALETTE[i % len(PALETTE)] for i, n in enumerate(sorted(names))}


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return 0
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def render(data, source_name, compact):
    meta = data["meta"]
    first, last = data["first_ts"], data["last_ts"]
    agents, errors, loops = data["agents"], data["errors"], data["fix_loops"]
    colours = colour_map({a["subagent"] for a in agents})
    tm, tok = data["time"], data["tokens_total"]

    n_err = sum(1 for e in errors if e["kind"] == "error")
    n_rej = sum(1 for e in errors if e["kind"] == "rejected")
    distinct = distinct_findings(data["findings"])
    sev = Counter((f["severity"] or "unrated") for f in distinct)
    sev_txt = " · ".join(f"{n} {s}" for s, n in sorted(sev.items(), key=lambda kv: SEV_ORDER.get(kv[0], 9)))
    tok_in = tok["input"] + tok["cache_write"] + tok["cache_read"]
    cached = (100 * tok["cache_read"] / tok_in) if tok_in else 0
    cards = [
        ("Wall time", fmt_dur(tm["wall_s"]),
         f'agents {fmt_dur(tm["agents_s"])} · you {fmt_dur(tm["human_wait_s"])} · '
         f'orchestrator {fmt_dur(tm["orchestrator_s"])}'),
        ("Agent runs", str(len(agents)), f'{sum(1 for a in agents if a.get("resume"))} resumed'),
        ("Fix loops", str(len(loops)),
         f'{fmt_dur(sum(lp["duration_s"] for lp in loops))} of rework' if loops else "none"),
        ("Findings", str(len(distinct)), sev_txt or "none recorded"),
        ("Output tokens", fmt_num(tok["output"]), "whole session, incl. subagents"),
        ("Input tokens", fmt_num(tok_in),
         f'{cached:.0f}% cache reads · {fmt_num(tok["cache_write"])} cache writes'),
        ("Errors", str(n_err), f"{n_rej} rejected tool calls"),
    ]
    cards_html = "\n".join(
        f'<div class="card"><div class="card-val">{esc(v)}</div>'
        f'<div class="card-lbl">{esc(l)}</div><div class="card-sub">{esc(sub)}</div></div>'
        for l, v, sub in cards)
    notes_html = ("".join(f'<li class="ins info">{esc(n)}</li>' for n in data.get("notes", [])))
    notes_html = f'<ul class="insights notes">{notes_html}</ul>' if notes_html else ""

    timeline_html, timeline_note = render_timeline(data, colours, compact)
    legend = " ".join(f'<span class="legend"><i style="background:{c}"></i>{esc(short_name(n))}</span>'
                      for n, c in colours.items())
    legend += (' <span class="legend"><i class="human-key"></i>you</span>'
               ' <span class="legend"><i class="loop-key"></i>fix loop</span>')
    has_sub = data.get("has_sub")
    scope_note = ('<p class="note">Includes tool calls and file access from '
                  'inside every subagent transcript, not just the top-level '
                  'session.</p>' if has_sub else "")
    ids = " · ".join(filter(None, [data.get("use_case"), data.get("change")]))
    title = ids or meta.get("title") or source_name
    span = f"{fmt_ts(first)} → {fmt_ts(last)}" if first else "—"
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    return HTML_TEMPLATE.format(
        title=esc(truncate(title, 90)),
        subtitle=esc(f"{source_name} · {span} · generated {generated}"),
        meta_line=esc(" · ".join(filter(None, [
            meta.get("gitBranch", ""), meta.get("cwd", ""),
            ", ".join(f"v{v}" for v in meta.get("versions", []))]))),
        cards=cards_html, notes=notes_html,
        insights=render_insights(agents, errors, loops),
        timeline_note=esc(timeline_note), legend=legend, timeline=timeline_html,
        findings=render_findings(data, colours),
        value=render_value_table(agents, colours, has_sub),
        runs=render_runs(agents, colours),
        context=render_context(data["ctx"], colours),
        ctx_title=" &amp; ".join(esc(d) for d in CONTEXT_DIRS),
        errors=render_error_panel(errors),
        tools=scope_note + render_tools(data["tool_stats_all"]),
        files=scope_note + render_files(data["files_all"]),
        feed=render_feed(data["timeline"], colours))


SEV_ORDER = {"blocking": 0, "high": 1, "medium": 2, "advisory": 3, "low": 4}


def status_class(st):
    return "bad" if st == "handed-back" else "good" if st.startswith("fixed") else "warn"


def distinct_findings(findings):
    """One entry per (gate, id): the fields from its first mention, with the
    status each later gate run gave it, in order."""
    out = {}
    for f in findings:
        key = (f["gate"], f["id"])
        if key not in out:
            out[key] = {**f, "statuses": []}
        if not out[key]["statuses"] or out[key]["statuses"][-1] != f["status"]:
            out[key]["statuses"].append(f["status"])
    return list(out.values())


def render_timeline(data, colours, compact):
    """One lane per agent type (resumed runs share their agent's lane), a lane for
    the human's waits, and a lane bracketing each fix loop."""
    agents = [a for a in data["agents"] if a["start"]]
    human = [tuple(h) for h in data["time"]["human_intervals"]]
    if not agents and not human:
        return '<p class="empty">No agent runs or waits recorded.</p>', ""
    first, last = data["first_ts"], data["last_ts"]
    ivs = [(a["start"], a["end"] or a["start"]) for a in agents] + human
    note = ""
    if compact and len(ivs) > 0:
        remap, span = build_remap(ivs)
        def x(t):
            return 100 * remap(t) / span
        note = "idle gaps collapsed; bar widths are still proportional to real time"
    else:
        span = (last - first).total_seconds() or 1
        def x(t):
            return 100 * (t - first).total_seconds() / span

    def bar(s, e, cls, colour, label, tip):
        left = x(s)
        width = max(0.6, x(e or s) - left)
        style = f"left:{left:.2f}%;width:{width:.2f}%" + (f";background:{colour}" if colour else "")
        return (f'<div class="tl-bar {cls}" style="{style}" title="{esc(tip)}">'
                f'<span>{esc(label)}</span></div>')

    def lane(label, bars, cls=""):
        return (f'<div class="tl-row {cls}"><div class="tl-label" title="{esc(label)}">{esc(label)}</div>'
                f'<div class="tl-track">{"".join(bars)}</div></div>')

    lanes = {}
    for a in sorted(agents, key=lambda a: a["start"]):
        lanes.setdefault(a["subagent"], []).append(a)
    rows = []
    for name, runs in lanes.items():
        bars = []
        for a in runs:
            status = ("pending" if a["pending"] else "caught" if a.get("caught")
                      else "error" if a["error"] else "ok")
            tk = run_tokens(a)
            tip = (f'{a["subagent"]} — {a["description"]}\n'
                   f'start {fmt_ts(a["start"])} · {fmt_dur(a["duration"])}'
                   f'{" · resumed" if a.get("resume") else ""}'
                   f'{" · " + a["verdict"] if a.get("verdict") and a["verdict"] != "—" else ""}'
                   f'\n{(a.get("sub") or {}).get("tool_calls", 0)} tool calls · '
                   f'{fmt_num(tk["output"])} output tokens')
            bars.append(bar(a["start"], a["end"], status + (" resumed" if a.get("resume") else ""),
                            colours[name], a["description"], tip))
        rows.append(lane(short_name(name), bars))
    if human:
        rows.append(lane("you", [bar(s, e, "human", None, "waiting", f"waiting on you · {fmt_dur((e - s).total_seconds())}")
                                for s, e in human], "human-row"))
    if data["fix_loops"]:
        bars = []
        for lp in data["fix_loops"]:
            label = f'{lp["gate"]}: {", ".join(lp["findings"]) or "sent back"}'
            tip = (f'{lp["gate"]} fix loop · {len(lp["fix_runs"])} fix run(s) · '
                   f'{"re-checked" if lp["recheck_run"] else "not re-checked"}\n'
                   f'{fmt_dur(lp["duration_s"])} · {lp["tool_calls"]} tool calls · '
                   f'{fmt_num(lp["tokens"]["output"])} output tokens')
            bars.append(bar(lp["start"], lp["end"], "loop", None, label, tip))
        rows.append(lane("fix loops", bars, "loop-row"))
    return "\n".join(rows), note


def render_findings(data, colours):
    gates = [a for a in data["agents"] if a["gate"]]
    if not gates:
        return '<p class="empty">No review or gate agents ran.</p>'
    rrows = []
    for a in gates:
        cls = "caught" if a.get("caught") else "clean"
        src = ('<span class="muted">from findings</span>' if a.get("verdict_source") == "findings"
               else '<span class="pill warn" title="no Run-log findings block; verdict guessed from '
                    'keywords">inferred</span>')
        n = len(a.get("findings") or [])
        rrows.append(f'''<tr>
          <td class="muted num">{esc(fmt_ts(a["start"]))}</td>
          <td><span class="agent-badge" style="background:{colours[a["subagent"]]}">{esc(short_name(a["subagent"]))}</span></td>
          <td>{esc(truncate(a["description"], 60))}{' <span class="muted">(resumed)</span>' if a.get("resume") else ''}</td>
          <td><span class="verdict {cls}">{esc(a.get("verdict") or "—")}</span></td>
          <td class="nw">{src}</td><td class="num">{n or "—"}</td>
          <td class="snip">{esc(truncate(a.get("snippet") or "", 160))}</td></tr>''')
    runs_table = f'''<table class="vtable">
      <thead><tr><th class="num">Start</th><th>Gate</th><th>Run</th><th>Verdict</th><th>Source</th>
      <th class="num">Findings</th><th>Summary</th></tr></thead><tbody>{"".join(rrows)}</tbody></table>'''

    fs = sorted(distinct_findings(data["findings"]),
                key=lambda f: (SEV_ORDER.get(f["severity"] or "", 9), f["gate"], f["id"]))
    if fs:
        frows = []
        for f in fs:
            trail = " ".join(f'<span class="pill {status_class(st)}">{esc(st)}</span>'
                             for st in f["statuses"])
            sv = f["severity"] or "—"
            svcls = "bad" if sv in ("blocking", "high") else "warn" if sv == "medium" else ""
            frows.append(f'''<tr>
              <td><b>{esc(f["id"])}</b></td><td>{esc(f["gate"])}</td>
              <td><span class="pill {svcls}">{esc(sv)}</span></td>
              <td>{esc(f["kind"] or "—")}</td>
              <td class="rule" title="{esc(f["rule"] or "")}">{esc(truncate(f["rule"] or "—", 30))}</td>
              <td class="trail">{trail}</td>
              <td class="snip" title="{esc((f["where"] or "") + chr(10) + (f.get("recommendation") or ""))}">{esc(truncate(f.get("root_cause") or "", 160))}</td></tr>''')
        ftable = f'''<p class="note">One row per finding; Status shows each gate run's verdict on it, in
          order. Hover the root cause for where it was and what would prevent it.</p>
          <table class="vtable">
          <thead><tr><th>Id</th><th>Gate</th><th>Severity</th><th>Kind</th><th>Rule</th>
          <th>Status</th><th>Root cause</th></tr></thead>
          <tbody>{"".join(frows)}</tbody></table>'''
    else:
        ftable = '<p class="empty">No gate wrote a Run-log findings block with entries.</p>'

    by_id = {a["id"]: a for a in data["agents"]}
    lrows = []
    for lp in data["fix_loops"]:
        fixes = ", ".join(truncate(by_id[r]["description"], 40) for r in lp["fix_runs"]) or "no fix run"
        recheck = (truncate(by_id[lp["recheck_run"]]["description"], 40) if lp["recheck_run"]
                   else '<span class="pill warn">not re-checked</span>')
        lrows.append(f'''<tr><td>{esc(lp["gate"])}</td><td>{esc(", ".join(lp["findings"]) or "—")}</td>
          <td>{esc(fixes)}</td><td>{recheck if not lp["recheck_run"] else esc(recheck)}</td>
          <td class="num">{esc(fmt_dur(lp["duration_s"]))}</td><td class="num">{lp["tool_calls"]}</td>
          <td class="num">{fmt_num(lp["tokens"]["output"])}</td></tr>''')
    ltable = (f'''<h3>Fix loops</h3><table class="vtable">
      <thead><tr><th>Gate</th><th>Sent back</th><th>Fixed by</th><th>Re-checked by</th>
      <th class="num">Time</th><th class="num">Tool calls</th><th class="num">Out tokens</th></tr></thead>
      <tbody>{"".join(lrows)}</tbody></table>''' if lrows else "")
    return (f'<h3>Gate runs</h3>{runs_table}<h3>Findings</h3>{ftable}{ltable}')


def render_value_table(agents, colours, has_sub=False):
    if not agents:
        return '<p class="empty">No agents.</p>'
    stats = defaultdict(lambda: {"runs": 0, "total": 0.0, "gate": False, "caught": 0, "err": 0,
                                 "calls": 0, "files": 0, "tokens": [], "models": set(),
                                 "efforts": set()})
    for a in agents:
        s = stats[a["subagent"]]
        s["runs"] += 1
        s["total"] += a["duration"] or 0
        s["gate"] = a["gate"]
        s["caught"] += int(bool(a.get("caught")))
        s["err"] += int(bool(a["error"]))
        if a.get("model"):
            s["models"].add(a["model"])
        s["efforts"].update(split_effort(a.get("effort")))
        sub = a.get("sub") or {}
        s["calls"] += sub.get("tool_calls", 0)
        s["files"] += len(sub.get("file_ops", {}))
        s["tokens"].append(run_tokens(a))
    rows = []
    for name, s in sorted(stats.items(), key=lambda kv: -kv[1]["total"]):
        avg = s["total"] / s["runs"] if s["runs"] else 0
        if s["gate"]:
            val = (f'<span class="pill good">caught {s["caught"]}/{s["runs"]}</span>' if s["caught"]
                   else f'<span class="pill warn">0/{s["runs"]}: approved all</span>')
        else:
            val = '<span class="muted">producer</span>'
        errc = f'<span class="pill bad">{s["err"]}</span>' if s["err"] else "0"
        tk = add_tokens(*s["tokens"])
        work = (f'<td class="num">{s["calls"]}</td><td class="num">{s["files"]}</td>'
                f'<td class="num muted">{fmt_num(tk["input"])}</td>'
                f'<td class="num muted">{fmt_num(tk["cache_write"])}</td>'
                f'<td class="num muted">{fmt_num(tk["cache_read"])}</td>'
                f'<td class="num">{fmt_num(tk["output"])}</td>') if has_sub else ""
        rows.append(f'''<tr>
          <td><i class="dot" style="background:{colours[name]}"></i>{esc(short_name(name))}{' <span class="gate-tag">gate</span>' if s["gate"] else ''}</td>
          <td class="nw">{esc(", ".join(short_model(m) for m in sorted(s["models"])) or "—")}</td>
          <td{' class="muted"' if join_known(s["efforts"]) == "unknown" else ''}>{esc(join_known(s["efforts"]))}</td>
          <td class="num">{s["runs"]}</td><td class="num">{fmt_dur(s["total"])}</td>
          <td class="num">{fmt_dur(avg)}</td>{work}
          <td>{val}</td><td class="num">{errc}</td></tr>''')
    work_head = ('<th class="num">Tool calls</th><th class="num">Files</th><th class="num">Input</th>'
                 '<th class="num">Cache write</th><th class="num">Cache read</th>'
                 '<th class="num">Output</th>') if has_sub else ""
    hint = ('<p class="note">Tool calls, files and tokens are the work done inside each agent, '
            'summed across its runs; a resumed run is credited with its own work.</p>'
            if has_sub else "")
    return f'''{hint}<table class="vtable">
      <thead><tr><th>Agent</th><th>Model</th><th>Effort</th><th class="num">Runs</th>
      <th class="num">Time</th><th class="num">Avg</th>{work_head}
      <th>Gate value</th><th class="num">Errors</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table>'''


def render_runs(agents, colours):
    """Every run, in order, with its own cost."""
    if not agents:
        return '<p class="empty">No agent runs.</p>'
    rows = []
    for a in agents:
        sub = a.get("sub") or {}
        tk = run_tokens(a)
        link = {"id": "", "resume": "resumed", "prompt": "linked by prompt"}.get(a.get("linked_by"),
                                                                             "no transcript")
        rows.append(f'''<tr>
          <td class="muted num">{esc(fmt_ts(a["start"]))}</td>
          <td><span class="agent-badge" style="background:{colours[a["subagent"]]}">{esc(short_name(a["subagent"]))}</span></td>
          <td>{esc(truncate(a["description"], 56))} <span class="muted">{esc(link)}</span></td>
          <td class="num">{esc(fmt_dur(a["duration"]))}</td><td class="num">{sub.get("tool_calls", 0)}</td>
          <td class="num muted">{fmt_num(tk["input"])}</td><td class="num muted">{fmt_num(tk["cache_write"])}</td>
          <td class="num muted">{fmt_num(tk["cache_read"])}</td><td class="num">{fmt_num(tk["output"])}</td>
          <td>{esc(a.get("verdict") or "")}</td></tr>''')
    return f'''<table class="vtable compact">
      <thead><tr><th class="num">Start</th><th>Agent</th><th>Run</th><th class="num">Time</th>
      <th class="num">Tool calls</th><th class="num">Input</th><th class="num">Cache write</th>
      <th class="num">Cache read</th><th class="num">Output</th><th>Verdict</th></tr></thead>
      <tbody>{"".join(rows)}</tbody></table>'''


def split_effort(e):
    """"medium, high" -> {"medium", "high"}; None / "unknown" -> {"unknown"}."""
    parts = {p.strip() for p in (e or "unknown").split(",") if p.strip()}
    return parts or {"unknown"}


def join_known(values):
    """Every value seen, "unknown" last — a run with nothing recorded stays
    visible even when other runs of the same agent recorded something."""
    known = sorted(v for v in values if v != "unknown")
    return ", ".join(known + (["unknown"] if "unknown" in values else [])) or "unknown"


def short_model(m):
    """claude-opus-4-8 -> opus-4-8; claude-sonnet-5 -> sonnet-5."""
    return re.sub(r"^claude-", "", m or "").replace("-latest", "")


def render_insights(agents, errors, loops=()):
    out = []
    by = defaultdict(list)
    for a in agents:
        if a["gate"]:
            by[short_name(a["subagent"])].append(a)
    loops_by = defaultdict(list)
    for lp in loops:
        loops_by[lp["gate"]].append(lp)
    for name, runs in sorted(by.items()):
        caught = [r for r in runs if r.get("caught")]
        if caught:
            total = sum(r["issues"] or 0 for r in caught)
            out.append(("good", f'{name} caught something in {len(caught)}/{len(runs)} runs'
                                f'{f" ({total} findings)" if total else ""}.'))
        else:
            out.append(("warn", f'{name} approved all {len(runs)} runs with no findings: either '
                                f'the work it checked was clean, or this gate is low-signal.'))
        lps = loops_by.get(name)
        if lps:
            out.append(("info", f'{name} sent work back {len(lps)} time(s); the fixes and re-checks '
                                f'took {fmt_dur(sum(lp["duration_s"] for lp in lps))}, '
                                f'{sum(lp["tool_calls"] for lp in lps)} tool calls and '
                                f'{fmt_num(sum(lp["tokens"]["output"] for lp in lps))} output tokens.'))
    ne = sum(1 for e in errors if e["kind"] == "error")
    nr = sum(1 for e in errors if e["kind"] == "rejected")
    if ne:
        top = Counter(e["tool"] for e in errors if e["kind"] == "error").most_common(1)[0]
        out.append(("bad", f'{ne} command or tool errors, most in {top[0]} ({top[1]}).'))
    if nr:
        out.append(("warn", f'{nr} tool calls you rejected: friction points where the agent '
                            f'guessed wrong.'))
    slow = sorted((a for a in agents if a["duration"]), key=lambda a: -a["duration"])[:1]
    if slow:
        a = slow[0]
        out.append(("info", f'Slowest run: {short_name(a["subagent"])} '
                            f'"{truncate(a["description"], 40)}" at {fmt_dur(a["duration"])}.'))
    if not out:
        return ""
    items = "\n".join(f'<li class="ins {c}">{esc(t)}</li>' for c, t in out)
    return f'<ul class="insights">{items}</ul>'


def render_error_panel(errors):
    if not errors:
        return '<p class="empty">No errors or rejected tool calls. 🎉</p>'
    rows = []
    for e in errors:
        cls = e["kind"]
        hint = summarize_tool_input(e["tool"], e["input"])
        rows.append(f'''
        <div class="err-item {cls}">
          <div class="err-time">{esc(fmt_ts(e["ts"]))}</div>
          <div class="err-body">
            <div><span class="tool-tag">{esc(e["tool"])}</span>
              <span class="pill {'bad' if cls=='error' else 'warn'}">{esc(cls)}</span></div>
            <div class="mono">{esc(truncate(hint, 160))}</div>
            <div class="err-msg">{esc(truncate(e["text"], 220))}</div>
          </div>
        </div>''')
    return "\n".join(rows)


def render_tools(stats):
    if not stats:
        return '<p class="empty">No tool calls.</p>'
    mx = max(s["count"] for s in stats.values())
    rows = []
    for name, s in sorted(stats.items(), key=lambda kv: -kv[1]["count"]):
        errc = f'<span class="pill bad">{s["err"]}</span>' if s["err"] else "—"
        rows.append(f'''<tr>
          <td>{esc(name)}</td>
          <td><div class="tool-bar-wrap"><div class="tool-bar" style="width:{100*s["count"]/mx:.1f}%"></div></div></td>
          <td class="num">{s["count"]}</td>
          <td class="num muted">{esc(fmt_dur(s["time"]))}</td>
          <td class="num">{errc}</td></tr>''')
    return f'''<table class="vtable">
      <thead><tr><th>Tool</th><th style="width:38%"></th><th class="num">Calls</th>
      <th class="num">Total time</th><th class="num">Errors</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table>'''


def render_files(files):
    if not files:
        return '<p class="empty">No files read, written, or edited.</p>'
    rows = []
    ordered = sorted(files.items(),
                     key=lambda kv: -(kv[1]["read"] + kv[1]["write"] + kv[1]["edit"]))
    for path, f in ordered[:60]:
        total = f["read"] + f["write"] + f["edit"]
        badges = []
        if f["write"]:
            badges.append(f'<span class="fop write">write ×{f["write"]}</span>')
        if f["edit"]:
            badges.append(f'<span class="fop edit">edit ×{f["edit"]}</span>')
        if f["read"]:
            badges.append(f'<span class="fop read">read ×{f["read"]}</span>')
        rows.append(f'''<tr>
          <td class="fpath">{esc(path)}</td>
          <td>{' '.join(badges)}</td>
          <td class="num muted">{total}</td></tr>''')
    more = (f'<p class="note">…and {len(ordered) - 60} more files.</p>'
            if len(ordered) > 60 else "")
    created = sum(1 for _, f in files.items() if f["write"] and not f["read"] and not f["edit"])
    shell = sum(f.get("shell", 0) for f in files.values())
    summary = (f'<p class="note">{len(files)} files touched · {created} written fresh (no prior '
               f'read) · counts incl. shell: {shell} operations came from shell commands such as '
               f'cat, sed, grep and redirects (common forms only). Claude Code\'s own files '
               f'are left out.</p>')
    return f'''{summary}<table class="vtable">
      <thead><tr><th>File</th><th>Operations</th><th class="num">Total</th></tr></thead>
      <tbody>{''.join(rows)}</tbody></table>{more}'''


def render_context(ctx, colours):
    per_file = ctx["per_file"]
    if not per_file and not ctx["never_read"]:
        return '<p class="empty">No ' + esc(" or ".join(d + "/" for d in CONTEXT_DIRS)) + ' docs were read.</p>'

    sizes = ctx.get("sizes", {})
    # density = influence per 1K tokens of the doc; used to spot wordy/low-signal docs
    dens = {p: (v["reads"] + v["refs"]) / (sizes[p] / 1000)
            for p, v in per_file.items() if sizes.get(p)}
    med_d = _median(list(dens.values()))
    med_sz = _median([sizes[p] for p in per_file if sizes.get(p)])
    total_read_cost = sum(v["reads"] * sizes.get(p, 0) for p, v in per_file.items())

    # per-file influence + efficiency table
    frows = []
    ordered = sorted(per_file.items(),
                     key=lambda kv: -(kv[1]["reads"] + kv[1]["refs"]))
    for path, v in ordered:
        influence = v["reads"] + v["refs"]
        inf_pct = (100 * v["informed"] / v["reads"]) if v["reads"] else 0
        size = sizes.get(path)
        density = dens.get(path)
        read_cost = v["reads"] * size if size else None
        readers = " ".join(
            f'<span class="rdr" style="background:{colours.get(r, "#888")}" '
            f'title="{esc(r)}"></span>' for r in sorted(v["readers"]))
        verdict = ""
        if density is not None and med_d:
            if density >= 1.5 * med_d:
                verdict = '<span class="pill good">dense</span>'
            elif density <= 0.5 * med_d and size >= med_sz:
                verdict = '<span class="pill warn">wordy / low-signal?</span>'
        if v["reads"] and not v["refs"]:
            verdict = '<span class="pill warn">read, never cited</span>'
        frows.append(f'''<tr>
          <td class="fpath">{esc(path)}</td>
          <td class="num muted">{fmt_num(size) if size else "—"}</td>
          <td class="num">{v["reads"]}</td>
          <td class="num muted">{inf_pct:.0f}%</td>
          <td class="num">{v["refs"]}</td>
          <td class="num"><b>{influence}</b></td>
          <td class="num muted">{f"{density:.1f}" if density is not None else "—"}</td>
          <td class="num muted">{fmt_num(read_cost) if read_cost else "—"}</td>
          <td>{readers}</td>
          <td>{verdict}</td></tr>''')
    file_table = f'''<table class="vtable">
      <thead><tr><th>Doc</th><th class="num" title="approx tokens (chars/4)">Size</th>
      <th class="num" title="Read tool and shell commands (cat, head, sed, grep…)">Reads incl. shell</th>
      <th class="num" title="share of reads before the agent's first write">Informed</th>
      <th class="num">Cited</th><th class="num">Influence</th>
      <th class="num" title="influence per 1K tokens of the doc — value per word">Value/1K</th>
      <th class="num" title="reads × size = context tokens spent re-reading it">Read cost</th>
      <th>Readers</th><th></th></tr></thead>
      <tbody>{''.join(frows)}</tbody></table>
      <p class="note">~{fmt_num(total_read_cost)} tokens were spent re-reading
      context docs across the run. <b>Value/1K</b> (influence per 1000 tokens of the
      doc) is the signal-density proxy: a large doc with low Value/1K is a
      bloat/trim candidate; confirm by trimming it and re-running with
      <code>--compare</code>.</p>'''

    # catches attributed to docs
    catches = ctx["catches_by_doc"]
    if catches:
        crows = " ".join(
            f'<span class="pill good">{esc(d)} → {n} catch{"es" if n>1 else ""}</span>'
            for d, n in sorted(catches.items(), key=lambda kv: -kv[1]))
        catch_html = (f'<p class="note">Reviewer catches that explicitly cite a doc '
                      f'— direct evidence the doc earned its place:</p><div>{crows}</div>')
    else:
        catch_html = ('<p class="note">No reviewer catch explicitly cited a '
                      f'{esc("/".join(CONTEXT_DIRS))} doc by filename.</p>')

    # flags
    flags = []
    if ctx["universe"] and ctx["never_read"]:
        flags.append('<li class="ins warn">Never read by any agent: '
                     + ", ".join(esc(f) for f in ctx["never_read"])
                     + " — dead weight, or context you assume is absorbed via CLAUDE.md.</li>")
    if ctx["read_never_ref"]:
        flags.append('<li class="ins info">Read but never cited in reasoning: '
                     + ", ".join(esc(f) for f in ctx["read_never_ref"])
                     + " — opened, but did it actually shape the output?</li>")
    flags_html = f'<ul class="insights">{"".join(flags)}</ul>' if flags else ""

    note = ('<p class="note"><b>Reading is not proof of benefit.</b> This shows the '
            'docs reach the agents and are used (Influence = reads + citations; '
            'Informed = read before the agent started writing). Reads include common '
            'shell commands (cat, head, sed, grep), so they are a close estimate, not exact. To prove they '
            '<em>help vs hinder</em>, compare two runs with <code>--compare</code> '
            '(full vs stripped context). Note CLAUDE.md is always in-context and '
            'is not counted here.</p>')
    return note + file_table + catch_html + flags_html


def render_feed(timeline, colours):
    feed = []
    for it in timeline:
        ts = fmt_ts(it["ts"])
        k = it["kind"]
        if k == "user":
            feed.append(feed_item(ts, "user", "You", truncate(it["text"], 600)))
        elif k == "assistant":
            feed.append(feed_item(ts, "assistant", "Claude", truncate(it["text"], 600)))
        elif k == "thinking":
            feed.append(feed_item(ts, "thinking", "Thinking", truncate(it["text"], 400)))
        elif k == "tool":
            feed.append(render_tool_feed(ts, it, colours))
    return "\n".join(feed) or '<p class="empty">Nothing to show.</p>'


def feed_item(ts, cls, who, body):
    return f'''<div class="feed {cls}"><div class="feed-time">{esc(ts)}</div>
      <div class="feed-body"><div class="feed-who">{esc(who)}</div>
      <div class="feed-text">{esc(body)}</div></div></div>'''


def render_tool_feed(ts, it, colours):
    tool = it["tool"]
    inp = it.get("input") or {}
    dur = fmt_dur(it.get("duration"))
    if tool == "Agent" or it.get("agent_view"):
        sub = inp.get("subagent_type", "agent")
        colour = colours.get(sub, "#6366f1")
        badge = f'<span class="agent-badge" style="background:{colour}">{esc(sub)}</span>'
        verdict = it.get("verdict")
        vhtml = ""
        if verdict and verdict != "—":
            vc = "caught" if it.get("caught") else "clean"
            vhtml = f' <span class="verdict {vc}">{esc(verdict)}</span>'
        res = (f'<div class="feed-result">{esc(truncate(it.get("result",""), 400))}</div>'
               if it.get("result") else "")
        stat = " ⚠ failed/rejected" if it.get("error") else ""
        return f'''<div class="feed tool agent"><div class="feed-time">{esc(ts)}</div>
          <div class="feed-body">
          <div class="feed-who">{badge} {"re-ran (resumed)" if it.get("resume") else "ran"} <span class="dur">{esc(dur)}</span>{vhtml}{esc(stat)}</div>
          <div class="feed-text">{esc(truncate(inp.get("description",""), 200))}</div>{res}</div></div>'''
    stat = ' <span class="err">⚠</span>' if it.get("error") else ""
    return f'''<div class="feed tool"><div class="feed-time">{esc(ts)}</div>
      <div class="feed-body"><div class="feed-who"><span class="tool-tag">{esc(tool)}</span>
      <span class="dur">{esc(dur)}</span>{stat}</div>
      <div class="feed-text mono">{esc(summarize_tool_input(tool, inp))}</div></div></div>'''


def summarize_tool_input(tool, inp):
    if not isinstance(inp, dict):
        return truncate(str(inp), 160)
    for key in ("command", "file_path", "path", "pattern", "query",
                "description", "url", "prompt", "message", "skill", "title"):
        if inp.get(key):
            return truncate(str(inp[key]).replace("\n", " "), 200)
    return truncate(json.dumps(inp)[:200], 200)


# --------------------------------------------------------------------------- #
HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — session report</title>
<style>
:root {{ --bg:#0f1117; --panel:#171a23; --panel2:#1e222d; --line:#2a2f3c;
  --fg:#e6e8ee; --muted:#9aa2b4; --accent:#6366f1;
  --good:#10b981; --warn:#f59e0b; --bad:#ef4444; }}
@media (prefers-color-scheme: light) {{ :root {{ --bg:#f6f7f9; --panel:#fff;
  --panel2:#f0f2f6; --line:#e2e5ec; --fg:#1c2027; --muted:#5c6472; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg);
  font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
.wrap {{ max-width:1120px; margin:0 auto; padding:32px 20px 90px; }}
h1 {{ font-size:24px; margin:0 0 4px; }}
.sub {{ color:var(--muted); font-size:13px; }}
.meta {{ color:var(--muted); font-size:12px; margin-top:4px; word-break:break-all; }}
h2 {{ font-size:14px; text-transform:uppercase; letter-spacing:.06em;
  color:var(--muted); margin:36px 0 12px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(135px,1fr));
  gap:12px; margin-top:22px; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:15px; }}
.card-val {{ font-size:21px; font-weight:650; }}
.card-lbl {{ color:var(--muted); font-size:12px; margin-top:2px; }}
.card-sub {{ color:var(--muted); font-size:11px; margin-top:6px; opacity:.85; }}
h3 {{ font-size:13px; margin:18px 0 8px; }} h3:first-child {{ margin-top:0; }}
details.diag > summary {{ cursor:pointer; list-style:none; }}
details.diag > summary::-webkit-details-marker {{ display:none; }}
details.diag > summary h2 {{ display:inline-block; }}
details.diag > summary h2::before {{ content:"\\25B8  "; }}
details.diag[open] > summary h2::before {{ content:"\\25BE  "; }}
details.inner {{ margin-top:14px; }}
details.inner > summary {{ cursor:pointer; color:var(--muted); font-size:12px; margin-bottom:8px; }}
.notes .ins {{ font-size:12px; }}
.snip {{ color:var(--muted); font-size:12px; }}
.vtable.compact td {{ padding:6px 8px; }}
.panel {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:18px; }}
.insights {{ list-style:none; padding:0; margin:18px 0 0; display:grid; gap:8px; }}
.ins {{ padding:10px 14px; border-radius:10px; border-left:3px solid var(--muted);
  background:var(--panel); font-size:13px; }}
.ins.good {{ border-color:var(--good); }} .ins.warn {{ border-color:var(--warn); }}
.ins.bad {{ border-color:var(--bad); }} .ins.info {{ border-color:var(--accent); }}
.legend {{ display:inline-flex; align-items:center; gap:6px; margin:0 12px 8px 0;
  font-size:12px; color:var(--muted); }}
.legend i {{ width:11px; height:11px; border-radius:3px; display:inline-block; }}
.note {{ color:var(--muted); font-size:12px; margin:-4px 0 10px; font-style:italic; }}
.tl-row {{ display:flex; align-items:center; gap:12px; margin:6px 0; }}
.tl-label {{ width:120px; flex:none; font-size:12px; color:var(--muted);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; text-align:right; }}
.tl-track {{ position:relative; flex:1; height:26px; background:var(--panel2); border-radius:6px; }}
.tl-bar {{ position:absolute; top:0; height:100%; border-radius:5px; min-width:3px;
  display:flex; align-items:center; overflow:hidden; opacity:.92;
  box-shadow:0 0 0 1px var(--panel) inset; }}
.tl-bar:hover {{ opacity:1; z-index:2; }}
.tl-bar span {{ font-size:11px; color:#fff; padding:0 6px; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; text-shadow:0 1px 1px rgba(0,0,0,.4); }}
.tl-bar.caught {{ outline:2px solid var(--good); outline-offset:-2px; }}
.tl-bar.error {{ outline:2px solid var(--bad); outline-offset:-2px; }}
.tl-bar.resumed {{ background-image:linear-gradient(90deg, rgba(0,0,0,.25) 0 3px, transparent 3px); }}
.tl-bar.pending {{ background-image:repeating-linear-gradient(45deg,
  rgba(255,255,255,.15) 0 6px, transparent 6px 12px)!important; }}
.tl-bar.human {{ background:repeating-linear-gradient(45deg, var(--muted) 0 4px, transparent 4px 8px);
  opacity:.55; }}
.tl-bar.human span {{ display:none; }}
.tl-bar.loop {{ background:rgba(245,158,11,.22); border:1px solid var(--warn); }}
.tl-bar.loop span {{ color:var(--warn); text-shadow:none; font-weight:600; }}
.human-row .tl-track, .loop-row .tl-track {{ height:20px; }}
.legend i.human-key {{ background:repeating-linear-gradient(45deg, var(--muted) 0 3px, transparent 3px 6px); }}
.legend i.loop-key {{ background:rgba(245,158,11,.3); border:1px solid var(--warn); }}
.vtable {{ width:100%; border-collapse:collapse; font-size:13px; }}
.vtable th {{ text-align:left; color:var(--muted); font-weight:600; font-size:12px;
  padding:8px 10px; border-bottom:1px solid var(--line); }}
.vtable td {{ padding:9px 10px; border-bottom:1px solid var(--line); }}
.dot {{ width:10px; height:10px; border-radius:3px; display:inline-block; margin-right:7px; }}
.gate-tag {{ font-size:10px; background:var(--accent); color:#fff; padding:1px 6px;
  border-radius:5px; margin-left:6px; }}
.pill {{ font-size:11px; padding:2px 9px; border-radius:20px; font-weight:600; white-space:nowrap; }}
.pill.good {{ background:rgba(16,185,129,.16); color:var(--good); }}
.pill.warn {{ background:rgba(245,158,11,.16); color:var(--warn); }}
.pill.bad {{ background:rgba(239,68,68,.16); color:var(--bad); }}
.muted {{ color:var(--muted); }}
.gate-item {{ border:1px solid var(--line); border-left:3px solid var(--muted);
  border-radius:10px; padding:12px 14px; margin:8px 0; background:var(--panel); }}
.gate-item.caught {{ border-left-color:var(--good); }}
.gate-item.clean {{ border-left-color:var(--muted); opacity:.85; }}
.gate-head {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
.gate-desc {{ margin-top:5px; font-size:13px; }}
.gate-snip {{ margin-top:7px; padding:8px 10px; background:var(--panel2);
  border-radius:8px; font-size:12px; color:var(--muted); }}
.verdict {{ font-size:11px; font-weight:700; padding:2px 9px; border-radius:6px; white-space:nowrap; }}
.vtable td.rule {{ font-family:ui-monospace,Menlo,monospace; font-size:11px; white-space:nowrap; }}
.vtable td.trail {{ white-space:normal; }} .trail .pill {{ display:inline-block; margin:1px 0; }}
.verdict.caught {{ background:rgba(16,185,129,.18); color:var(--good); }}
.verdict.clean {{ background:var(--panel2); color:var(--muted); }}
.err-item {{ display:flex; gap:12px; padding:11px 0; border-top:1px solid var(--line); }}
.err-item .err-time {{ width:66px; flex:none; color:var(--muted); font-size:12px; }}
.err-body {{ flex:1; min-width:0; }}
.err-msg {{ margin-top:5px; font-size:12px; color:var(--bad); white-space:pre-wrap; }}
.err-item.rejected .err-msg {{ color:var(--warn); }}
.tool-bar-wrap {{ background:var(--panel2); border-radius:5px; height:14px; min-width:60px; }}
.tool-bar {{ height:100%; background:var(--accent); border-radius:5px; }}
.vtable td.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.vtable td.nw {{ white-space:nowrap; }}
.vtable th.num {{ text-align:right; }}
.fpath {{ font-family:ui-monospace,Menlo,monospace; font-size:12px; word-break:break-all; }}
.fop {{ display:inline-block; font-size:10px; font-weight:600; padding:1px 7px;
  border-radius:20px; margin-right:5px; }}
.fop.write {{ background:rgba(99,102,241,.16); color:var(--accent); }}
.fop.edit {{ background:rgba(245,158,11,.16); color:var(--warn); }}
.fop.read {{ background:var(--panel2); color:var(--muted); }}
.rdr {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:3px; }}
.vtable code {{ font-size:12px; }}
.feed {{ display:flex; gap:14px; padding:12px 0; border-top:1px solid var(--line); }}
.feed-time {{ width:66px; flex:none; color:var(--muted); font-size:12px;
  font-variant-numeric:tabular-nums; }}
.feed-body {{ flex:1; min-width:0; }}
.feed-who {{ font-size:12px; font-weight:600; margin-bottom:3px; }}
.feed-text {{ white-space:pre-wrap; word-wrap:break-word; }}
.feed-text.mono {{ font-family:ui-monospace,Menlo,monospace; font-size:12px; color:var(--muted); }}
.feed-result {{ margin-top:6px; padding:8px 10px; background:var(--panel2);
  border-radius:8px; font-size:12px; color:var(--muted); white-space:pre-wrap; }}
.feed.user .feed-who {{ color:var(--good); }}
.feed.assistant .feed-who {{ color:var(--accent); }}
.feed.thinking {{ opacity:.7; }} .feed.thinking .feed-who {{ color:#a855f7; }}
.feed.thinking .feed-text {{ font-style:italic; }}
.agent-badge, .tool-tag {{ display:inline-block; padding:1px 8px; border-radius:6px;
  color:#fff; font-size:11px; font-weight:600; }}
.tool-tag {{ background:var(--panel2); color:var(--muted); }}
.dur {{ color:var(--muted); font-weight:400; font-size:11px; }}
.err {{ color:var(--bad); }} .empty {{ color:var(--muted); font-style:italic; }}
.filters {{ margin:10px 0 4px; display:flex; gap:8px; flex-wrap:wrap; }}
.filters button {{ background:var(--panel2); color:var(--fg); border:1px solid var(--line);
  border-radius:20px; padding:4px 13px; font-size:12px; cursor:pointer; }}
.filters button.active {{ background:var(--accent); color:#fff; border-color:var(--accent); }}
</style></head>
<body><div class="wrap">
  <h1>{title}</h1>
  <div class="sub">{subtitle}</div>
  <div class="meta">{meta_line}</div>
  <div class="cards">{cards}</div>
  {notes}
  {insights}

  <h2>Timeline</h2>
  <div class="note">{timeline_note}</div>
  <div style="margin-bottom:10px">{legend}</div>
  <div class="panel">{timeline}</div>

  <h2>Findings</h2>
  <div class="panel">{findings}</div>

  <h2>Agents</h2>
  <div class="panel">{value}
    <details class="inner"><summary>Every run</summary>{runs}</details></div>

  <h2>Context — {ctx_title}</h2>
  <div class="panel">{context}</div>

  <details class="diag"><summary><h2>Errors &amp; friction</h2></summary>
  <div class="panel">{errors}</div></details>

  <details class="diag"><summary><h2>Tool usage</h2></summary>
  <div class="panel">{tools}</div></details>

  <details class="diag"><summary><h2>Files touched</h2></summary>
  <div class="panel">{files}</div></details>

  <details class="diag"><summary><h2>Activity feed</h2></summary>
  <div class="filters">
    <button data-f="all" class="active">All</button>
    <button data-f="user">Prompts</button>
    <button data-f="assistant">Decisions</button>
    <button data-f="agent">Agents</button>
    <button data-f="tool">Tools</button>
    <button data-f="thinking">Thinking</button>
  </div>
  <div id="feed">{feed}</div></details>
</div>
<script>
const btns=[...document.querySelectorAll('.filters button')];
const items=[...document.querySelectorAll('#feed .feed')];
btns.forEach(b=>b.onclick=()=>{{
  btns.forEach(x=>x.classList.remove('active')); b.classList.add('active');
  const f=b.dataset.f;
  items.forEach(it=>{{
    let show = f==='all' || it.classList.contains(f)
      || (f==='tool' && it.classList.contains('tool') && !it.classList.contains('agent'));
    it.style.display = show ? '' : 'none';
  }});
}});
</script>
</body></html>"""


# --------------------------------------------------------------------------- #
# Compare mode — diff two runs (e.g. full vs stripped context) on outcomes
# --------------------------------------------------------------------------- #

def session_metrics(path):
    """Load a session and reduce it to the scalar outcome metrics used to
    compare two runs in an ablation."""
    data = analyze_session(path)
    ctx = data["ctx"]
    agents = data["agents"]
    first, last = data["first_ts"], data["last_ts"]
    tool_stats = data["tool_stats_all"]
    files = data["files_all"]
    out_tok = data["tokens_total"]["output"]
    per_file = ctx["per_file"]

    return {
        "name": Path(path).stem,
        "wall": (last - first).total_seconds() if first and last else 0,
        "agent_runs": len(agents),
        "gate_runs": sum(1 for a in agents if a["gate"]),
        "issues_caught": sum(1 for a in agents if a.get("caught")),
        "errors": sum(1 for e in data["errors"] if e["kind"] == "error"),
        "rejections": sum(1 for e in data["errors"] if e["kind"] == "rejected"),
        "tool_calls": sum(s["count"] for s in tool_stats.values()),
        "files": len(files),
        "out_tokens": out_tok,
        "ctx_reads": sum(v["reads"] for v in per_file.values()),
        "ctx_docs": len(per_file),
        "ctx_catches": sum(ctx["catches_by_doc"].values()),
    }


# metric key -> (label, better-direction, formatter)
COMPARE_METRICS = [
    ("wall", "Wall-clock", "neutral", fmt_dur),
    ("agent_runs", "Agent runs", "neutral", str),
    ("gate_runs", "Review-gate runs", "neutral", str),
    ("issues_caught", "Issues caught by gates", "neutral", str),
    ("errors", "Errors", "lower", str),
    ("rejections", "Rejections", "lower", str),
    ("tool_calls", "Tool calls (incl. subagents)", "lower", str),
    ("files", "Files touched (incl. subagents)", "neutral", str),
    ("out_tokens", "Output tokens (cost)", "lower", fmt_num),
    ("ctx_reads", "Context-doc reads", "neutral", str),
    ("ctx_docs", "Distinct context docs used", "neutral", str),
    ("ctx_catches", "Catches citing a context doc", "higher", str),
]


def render_compare(a, b, label_a, label_b):
    rows = []
    for key, label, better, fmt in COMPARE_METRICS:
        va, vb = a[key], b[key]
        delta = vb - va
        cls = ""
        if better != "neutral" and delta != 0:
            improved = (delta < 0) if better == "lower" else (delta > 0)
            cls = "good" if improved else "bad"
        sign = "+" if delta > 0 else "−"
        if delta == 0:
            dtxt = "—"
        elif fmt in (fmt_dur, fmt_num):
            dtxt = sign + fmt(abs(delta))
        else:
            dtxt = sign + str(abs(delta))
        rows.append(f'''<tr>
          <td>{esc(label)}</td>
          <td class="num">{esc(fmt(va))}</td>
          <td class="num">{esc(fmt(vb))}</td>
          <td class="num {cls}"><b>{esc(dtxt)}</b></td></tr>''')
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    return COMPARE_TEMPLATE.format(
        label_a=esc(label_a), label_b=esc(label_b),
        name_a=esc(a["name"]), name_b=esc(b["name"]),
        rows="".join(rows), generated=esc(generated))


COMPARE_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{label_a} vs {label_b} — session compare</title>
<style>
:root {{ --bg:#0f1117; --panel:#171a23; --panel2:#1e222d; --line:#2a2f3c;
  --fg:#e6e8ee; --muted:#9aa2b4; --good:#10b981; --bad:#ef4444; }}
@media (prefers-color-scheme: light) {{ :root {{ --bg:#f6f7f9; --panel:#fff;
  --panel2:#f0f2f6; --line:#e2e5ec; --fg:#1c2027; --muted:#5c6472; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg);
  font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
.wrap {{ max-width:820px; margin:0 auto; padding:32px 20px 80px; }}
h1 {{ font-size:23px; margin:0 0 4px; }}
.sub {{ color:var(--muted); font-size:13px; margin-bottom:22px; }}
table {{ width:100%; border-collapse:collapse; }}
th, td {{ padding:10px 12px; border-bottom:1px solid var(--line); text-align:left; }}
th {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.05em; }}
td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.good {{ color:var(--good); }} .bad {{ color:var(--bad); }}
.note {{ color:var(--muted); font-size:13px; margin-top:20px;
  background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }}
.note b {{ color:var(--fg); }}
</style></head>
<body><div class="wrap">
  <h1>{label_a} <span style="color:var(--muted)">vs</span> {label_b}</h1>
  <div class="sub">{name_a} → {name_b} · generated {generated}</div>
  <table>
    <thead><tr><th>Metric</th><th class="num">{label_a}</th>
    <th class="num">{label_b}</th><th class="num">Δ</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <div class="note">
    <b>How to read this.</b> Δ is {label_b} minus {label_a}. Green/red is applied
    only where direction is unambiguous — fewer <b>errors</b>, <b>rejections</b>,
    <b>tokens</b> is better; more <b>catches that cite a context doc</b> is better.
    The rest (runs, issues caught, files) are shown without a verdict because
    their meaning depends on your hypothesis: e.g. if the stripped-context run
    catches <em>more</em> issues late, the context was preventing defects; if it
    catches <em>fewer</em> but ships worse code, the gates lost their reference.
    Pair this with a look at the two full reports.
  </div>
</div></body></html>"""


# --------------------------------------------------------------------------- #
SUMMARY_SCHEMA = 1


def _rel(path):
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if dt else None


def run_summary(data, out):
    """The run facts a retrospective records and a trends report reads: what ran,
    with full model IDs, what each run cost, what the gates found and the fix loops
    they caused. A value that differs across runs is a comma-separated list;
    anything the transcript didn't record is "unknown"."""
    per = defaultdict(lambda: {"models": set(), "efforts": set(), "runs": 0, "duration": 0.0,
                               "calls": 0, "tokens": []})
    runs = []
    for a in data["agents"]:
        name = short_name(a["subagent"])
        sub = a.get("sub") or {}
        p = per[name]
        p["runs"] += 1
        p["models"].add(a.get("model") or "unknown")
        p["efforts"].update(split_effort(a.get("effort")))
        p["duration"] += a["duration"] or 0
        p["calls"] += sub.get("tool_calls", 0)
        p["tokens"].append(run_tokens(a))
        runs.append({
            "id": a["id"], "agent": name, "description": a["description"],
            "start": _iso(a["start"]), "duration_s": round(a["duration"] or 0, 1),
            "resumed": bool(a.get("resume")), "linked_by": a.get("linked_by"),
            "tool_calls": sub.get("tool_calls", 0), "tokens": run_tokens(a),
            "verdict": a.get("verdict"), "verdict_source": a.get("verdict_source"),
            "findings": [f["id"] for f in (a.get("findings") or [])],
        })
    agents = {name: {"model": join_known(p["models"]), "effort": join_known(p["efforts"]),
                     "runs": p["runs"], "duration_s": round(p["duration"], 1),
                     "tool_calls": p["calls"], "tokens": add_tokens(*p["tokens"])}
              for name, p in sorted(per.items())}
    versions = data["meta"].get("versions") or []
    return {
        "schema": SUMMARY_SCHEMA,
        "session": data["meta"].get("sessionId") or "unknown",
        "report": _rel(out),
        "summary": _rel(summary_path(out)),
        "claude_code": (versions[0] if len(versions) == 1 else versions) or "unknown",
        "use_case": data.get("use_case"), "change": data.get("change"),
        "orchestrator": {"model": data.get("main_model") or "unknown",
                         "effort": data.get("main_effort") or "unknown",
                         "tokens": tokens4(data["tokens"])},
        "agents": agents,
        "time": {k: v for k, v in data["time"].items() if k != "human_intervals"},
        "tokens": data["tokens_total"],
        "runs": runs,
        "findings": data["findings"],
        "fix_loops": [{k: v for k, v in lp.items() if k not in ("start", "end")}
                      for lp in data["fix_loops"]],
        "notes": data.get("notes", []),
    }


def summary_path(out):
    name = out.name[:-len(".report.html")] if out.name.endswith(".report.html") else out.stem
    return out.with_name(name + ".summary.json")


def write_outputs(data, source_name, out, compact):
    """Write the HTML report and the summary file beside it; return the summary."""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(data, source_name, compact), encoding="utf-8")
    summary = run_summary(data, out)
    summary_path(out).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
    return summary


def main():
    global CONTEXT_DIRS, CONTEXT_RE
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session", help="path to the session .jsonl log")
    ap.add_argument("-o", "--output", help="output HTML path (default: "
                    "<out-dir>/<session>.report.html)")
    ap.add_argument("--out-dir", default="reports/sessions",
                    help="directory for reports, relative to the current project "
                    "so reports live alongside the code (default: reports/sessions)")
    ap.add_argument("--context-dirs", default=",".join(CONTEXT_DIRS),
                    help="comma-separated project folders whose *.md docs count as "
                    "curated context in the Context-ingestion panel "
                    "(default: domain,standards)")
    ap.add_argument("--compact", action="store_true",
                    help="collapse idle gaps in the agent timeline")
    ap.add_argument("--no-subagents", action="store_true",
                    help="ignore the subagents/ transcripts (top-level only)")
    ap.add_argument("--compare", metavar="OTHER.jsonl",
                    help="produce an A/B comparison of two runs (e.g. full vs "
                    "stripped context) instead of a normal report; SESSION is A, "
                    "this is B")
    ap.add_argument("--label-a", default="Run A", help="label for the SESSION run")
    ap.add_argument("--label-b", default="Run B", help="label for the --compare run")
    ap.add_argument("--open", action="store_true",
                    help="open the report in a browser when done")
    ap.add_argument("--summary", action="store_true",
                    help="print the run summary (the same JSON object written to "
                    "<session>.summary.json) instead of the status lines")
    args = ap.parse_args()

    CONTEXT_DIRS = tuple(d.strip().strip("/") for d in args.context_dirs.split(",")
                         if d.strip())
    CONTEXT_RE = context_re(CONTEXT_DIRS)
    out_dir = Path.cwd() / args.out_dir

    src = Path(args.session)
    if not src.exists():
        ap.error(f"no such file: {src}")

    # ---- compare mode: diff two runs on outcome metrics ----------------- #
    if args.compare:
        other = Path(args.compare)
        if not other.exists():
            ap.error(f"no such file: {other}")
        m_a, m_b = session_metrics(src), session_metrics(other)
        out = (Path(args.output) if args.output else
               out_dir / f"compare-{src.stem}-vs-{other.stem}.report.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_compare(m_a, m_b, args.label_a, args.label_b),
                       encoding="utf-8")
        print(f"compared {args.label_a} vs {args.label_b}")
        print(f"wrote {out}")
        if args.open:
            webbrowser.open(out.resolve().as_uri())
        return

    try:
        data = analyze_session(src, no_subagents=args.no_subagents)
    except ValueError as e:
        ap.error(str(e))
    # default: keep reports with the project, under --out-dir
    out = Path(args.output) if args.output else out_dir / (src.stem + ".report.html")
    summary = write_outputs(data, src.name, out, args.compact)

    if args.summary:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        if args.open:
            webbrowser.open(out.resolve().as_uri())
        return

    subs = data["subagents"]
    n_err = sum(1 for e in data["errors"] if e["kind"] == "error")
    sub_note = (f" · {len(subs)} subagent transcripts "
                f"({sum(s['tool_calls'] for s in subs.values())} inner tool calls)"
                if subs else " · no subagent transcripts found")
    print(f"{len(data['agents'])} agent runs · {len(data['findings'])} findings · "
          f"{len(data['fix_loops'])} fix loops · {n_err} errors{sub_note}")
    for n in data.get("notes", []):
        print(f"note: {n}")
    print(f"wrote {out}")
    print(f"wrote {summary_path(out)}")
    if args.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
