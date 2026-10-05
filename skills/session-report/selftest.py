#!/usr/bin/env python3
"""Self-test for session_report.py. Builds small synthetic sessions in a temp
folder (never real transcripts), runs the analysis on each, and checks the
numbers the session-report spec promises. Standard library only.

    python3 skills/session-report/selftest.py      # exit 0 = pass

Fixtures:
  A  resumed agents with meta files, a QA fix loop, two reviewers whose
     prompts share their first 120 characters, findings blocks.
  B  the same run with no meta files and no resume markers, plus a reviewer
     with no findings block.
  C  no agents: shell reads of context docs, an internal tool-result read, a
     question to the user and a wait for the next prompt.
"""
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import session_report as sr  # noqa: E402

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
CWD = "/proj"
USAGE = {"input_tokens": 10, "output_tokens": 5,
         "cache_creation_input_tokens": 100, "cache_read_input_tokens": 1000}
FAILS = []


def ts(sec):
    return (T0 + timedelta(seconds=sec)).isoformat().replace("+00:00", "Z")


class Transcript:
    """Builds one .jsonl transcript and tallies the tokens it records."""

    def __init__(self, session="sess"):
        self.lines, self.session, self.n = [], session, 0
        self.tokens = {k: 0 for k in USAGE}

    def _ev(self, sec, etype, message, **extra):
        self.lines.append({"type": etype, "timestamp": ts(sec), "sessionId": self.session,
                           "cwd": CWD, "version": "2.1.0", "gitBranch": "feat/x",
                           "message": message, **extra})

    def prompt(self, sec, text):
        self._ev(sec, "user", {"role": "user", "content": text})

    def say(self, sec, text, usage=None):
        u = usage or USAGE
        for k in self.tokens:
            self.tokens[k] += u[k]
        self._ev(sec, "assistant", {"role": "assistant", "model": "claude-opus-5-5",
                                    "content": [{"type": "text", "text": text}], "usage": u})

    def tool(self, sec, name, inp, result_sec, result="ok", tid=None, is_error=False):
        self.n += 1
        tid = tid or f"toolu_{self.session}_{self.n}"
        for k in self.tokens:
            self.tokens[k] += USAGE[k]
        self._ev(sec, "assistant", {"role": "assistant", "model": "claude-opus-5-5",
                                    "content": [{"type": "tool_use", "id": tid, "name": name,
                                                 "input": inp}], "usage": USAGE})
        self._ev(result_sec, "user", {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tid, "content": result,
             "is_error": is_error}]})
        return tid

    def write(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(l) for l in self.lines) + "\n", encoding="utf-8")


REVIEW_PROMPT = ("Review the plan for change renew-loan against the profile and standards. "
                 "Check every task names its test and every scenario has a test. ")
QA_BLOCK = """NOT READY.

## Run-log findings
- **Q1** · kind: test-gap · severity: high
  · rule: `standards/testing.md §2` · where: `src/a.ts:10` · status: handed-back (defect for the junior dev)
  - root cause: task omission.
  - recommendation: none: one-off
- **Q2** · kind: code-defect · severity: medium · rule: — · where: `src/b.ts:3` · status: handed-back
- **Q3** · kind: test-gap · severity: low · rule: — · where: `src/c.ts:1` · status: handed-back
"""


def build_pipeline(root, with_meta, with_markers, extra_gate):
    """Fixtures A and B. Returns (session path, expected token totals)."""
    main = Transcript("sessA")
    subs = {}

    def sub(aid, prompt, start, steps, meta_tid, desc, agent):
        t = Transcript(aid)
        t.prompt(start, prompt)
        for kind, sec, payload in steps:
            if kind == "tool":
                t.tool(sec, payload[0], payload[1], sec + 1)
            elif kind == "say":
                t.say(sec, payload)
            elif kind == "resume" and with_markers:
                t.prompt(sec, "The coordinator sent a message while you were working:\n" + payload)
        subs[aid] = (t, meta_tid, desc, agent)

    main.prompt(0, "Run the pipeline on use-cases/UC-007-renew-loan.md")
    # two reviewers whose prompts share their first 120 characters
    main.tool(5, "Agent", {"subagent_type": "sdlc-pipeline:spec-reviewer",
                           "description": "Review plan (1)", "prompt": REVIEW_PROMPT + "First pass."},
              60, "APPROVE\n\n## Run-log findings\nNone\n\nagentId: agR1", tid="toolu_A3")
    sub("agR1", REVIEW_PROMPT + "First pass.", 6,
        [("tool", 10, ("Bash", {"command": "cat standards/testing.md"})),
         ("tool", 20, ("Read", {"file_path": "/proj/openspec/changes/renew-loan/tasks.md"})),
         ("say", 50, "APPROVE")], "toolu_A3", "Review plan (1)", "sdlc-pipeline:spec-reviewer")
    main.tool(61, "Agent", {"subagent_type": "sdlc-pipeline:spec-reviewer",
                            "description": "Review plan (2)", "prompt": REVIEW_PROMPT + "Second pass."},
              120, "APPROVE\n\n## Run-log findings\nNone\n\nagentId: agR2", tid="toolu_A4")
    sub("agR2", REVIEW_PROMPT + "Second pass.", 62,
        [("tool", 65 + i, ("Bash", {"command": f"grep -n task openspec/changes/renew-loan/tasks.md # {i}"}))
         for i in range(5)] + [("say", 110, "APPROVE")],
        "toolu_A4", "Review plan (2)", "sdlc-pipeline:spec-reviewer")
    # Gate 1 approval
    main.tool(125, "AskUserQuestion", {"questions": [{"question": "Approve the plan?"}]}, 245, "yes")
    # junior-dev builds; qa rejects; junior-dev fixes; qa re-verifies
    main.tool(250, "Agent", {"subagent_type": "sdlc-pipeline:junior-dev",
                             "description": "Implement UC-007", "prompt": "Implement the change renew-loan."},
              550, "Done.\nagentId: agJ1", tid="toolu_A1")
    sub("agJ1", "Implement the change renew-loan.", 251,
        [("tool", 255, ("Bash", {"command": "openspec status --change renew-loan --json"})),
         ("tool", 300, ("Write", {"file_path": "/proj/src/a.ts", "content": "x"})),
         ("tool", 360, ("Edit", {"file_path": "/proj/src/b.ts"})),
         ("say", 540, "Implemented."),
         ("resume", 735, "Fix Q1-Q3")]
        + [("tool", 740 + 10 * i, ("Bash", {"command": f"sed -i 's/a/b/' src/a.ts # {i}"}))
           for i in range(12)]
        + [("say", 900, "Fixed.")], "toolu_A1", "Implement UC-007", "sdlc-pipeline:junior-dev")
    main.tool(555, "Agent", {"subagent_type": "sdlc-pipeline:qa",
                             "description": "Verify UC-007", "prompt": "Verify the change renew-loan."},
              720, QA_BLOCK + "\nagentId: agQ1", tid="toolu_A2")
    sub("agQ1", "Verify the change renew-loan.", 556,
        [("tool", 560, ("Bash", {"command": "cat standards/testing.md src/a.ts"})),
         ("tool", 600, ("Bash", {"command": "npm test"})),
         ("say", 715, "NOT READY"),
         ("resume", 915, "Re-verify after fixes"),
         ("tool", 920, ("Bash", {"command": "npm test"})),
         ("say", 950, "READY")], "toolu_A2", "Verify UC-007", "sdlc-pipeline:qa")
    main.tool(730, "SendMessage", {"to": "agJ1", "summary": "Fix QA defects Q1-Q3",
                                   "message": "Fix Q1-Q3"},
              910, '{"resumedAgentId": "agJ1"} Fixed all three.', tid="toolu_S1")
    main.tool(912, "SendMessage", {"to": "agQ1", "summary": "Re-verify after fixes",
                                   "message": "Re-verify after fixes"},
              960, '{"resumedAgentId": "agQ1"} READY.\n\n## Run-log findings\n'
                   "- **Q1** · kind: test-gap · severity: high · rule: — · where: — · status: fixed-by-rework\n",
              tid="toolu_S2")
    if extra_gate:
        main.tool(965, "Agent", {"subagent_type": "sdlc-pipeline:spec-reviewer",
                                 "description": "Review wording", "prompt": "Review the wording."},
                  990, "REQUEST CHANGES: the design misses a risk.\nagentId: agR9", tid="toolu_B3")
    main.say(1000, "Pipeline finished.")

    path = root / "sessA.jsonl"
    main.write(path)
    totals = dict(main.tokens)
    for aid, (t, tid, desc, agent) in subs.items():
        t.write(root / "sessA" / "subagents" / f"agent-{aid}.jsonl")
        if with_meta:
            (root / "sessA" / "subagents" / f"agent-{aid}.meta.json").write_text(json.dumps(
                {"agentType": agent, "description": desc, "toolUseId": tid, "spawnDepth": 1}))
        for k in totals:
            totals[k] += t.tokens[k]
    return path, totals


def build_no_agents(root):
    t = Transcript("sessC")
    t.prompt(0, "check the standards")
    t.tool(5, "Bash", {"command": "cat standards/testing.md && head -n 5 domain/glossary.md"}, 6)
    t.tool(10, "Read", {"file_path": "/Users/x/.claude/projects/-proj/sessC/tool-results/abc.txt"}, 11)
    t.tool(12, "Read", {"file_path": "/proj/src/app.ts"}, 13)
    t.tool(20, "AskUserQuestion", {"questions": [{"question": "Approve?"}]}, 200, "yes")
    t.say(205, "Waiting for you.")
    t.prompt(625, "next")
    t.say(630, "Done.")
    path = root / "sessC.jsonl"
    t.write(path)
    proj = root / "projC"
    for rel in ("standards/testing.md", "domain/glossary.md", "domain/overview.md"):
        (proj / rel).parent.mkdir(parents=True, exist_ok=True)
        (proj / rel).write_text("# doc\n", encoding="utf-8")
    return path, proj


def check(name, got, want):
    if got != want:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")


def runs_by_id(data):
    return {a["id"]: a for a in data["agents"]}


def tool_calls(run):
    return (run.get("sub") or {}).get("tool_calls")


def test_pipeline(root):
    path, totals = build_pipeline(root / "A", with_meta=True, with_markers=True, extra_gate=False)
    data = sr.analyze_session(path)
    r = runs_by_id(data)
    for tid, want in (("toolu_A3", 2), ("toolu_A4", 5), ("toolu_A1", 3), ("toolu_S1", 12),
                      ("toolu_A2", 2), ("toolu_S2", 1)):
        check(f"A {tid} tool calls", tool_calls(r[tid]), want)
    for tid in ("toolu_A1", "toolu_A2", "toolu_A3", "toolu_A4"):
        check(f"A {tid} linked_by", r[tid].get("linked_by"), "id")
    check("A notes", [n for n in data["notes"] if "prompt" in n or "marker" in n], [])

    f = {(x["run"], x["id"]): x for x in data["findings"]}
    q1 = f.get(("toolu_A2", "Q1"), {})
    check("A Q1 fields", {k: q1.get(k) for k in ("gate", "kind", "severity", "rule", "where", "status")},
          {"gate": "qa", "kind": "test-gap", "severity": "high", "rule": "standards/testing.md §2",
           "where": "src/a.ts:10", "status": "handed-back"})
    check("A Q1 root cause", q1.get("root_cause"), "task omission.")
    check("A qa verdict", (r["toolu_A2"]["verdict"], r["toolu_A2"]["verdict_source"]),
          ("handed-back", "findings"))
    check("A reviewer verdict", (r["toolu_A3"]["verdict"], r["toolu_A3"]["verdict_source"]),
          ("clean", "findings"))

    loops = data["fix_loops"]
    check("A loop count", len(loops), 1)
    if loops:
        lp = loops[0]
        check("A loop", (lp["gate"], lp["started_by"], lp["findings"], lp["fix_runs"], lp["recheck_run"]),
              ("qa", "toolu_A2", ["Q1", "Q2", "Q3"], ["toolu_S1"], "toolu_S2"))
        check("A loop tool calls", lp["tool_calls"], 13)

    check("A tokens", data["tokens_total"], {"input": totals["input_tokens"],
                                             "cache_write": totals["cache_creation_input_tokens"],
                                             "cache_read": totals["cache_read_input_tokens"],
                                             "output": totals["output_tokens"]})
    t = data["time"]
    check("A time adds up", round(t["agents_s"] + t["human_wait_s"] + t["orchestrator_s"]), round(t["wall_s"]))
    check("A gate wait", t["human_wait_s"], 120.0)
    check("A header", (data["use_case"], data["change"]), ("UC-007", "renew-loan"))

    # outputs: printed summary == written summary; layout order; diagnostics closed
    out = root / "A" / "out" / "sessA.report.html"
    proc = subprocess.run([sys.executable, str(HERE / "session_report.py"), str(path), "-o", str(out),
                           "--summary", "--compact"], capture_output=True, text=True, cwd=str(root))
    check("A --summary exit", proc.returncode, 0)
    written = json.loads((out.parent / "sessA.summary.json").read_text(encoding="utf-8"))
    check("A printed == written", json.loads(proc.stdout or "{}"), written)
    check("A summary agents.qa.runs", written["agents"]["qa"]["runs"], 2)
    check("A summary schema", written["schema"], 1)
    html = out.read_text(encoding="utf-8")
    heads = ["Timeline", "Findings", "Agents", "Context"]
    pos = [html.find(f"<h2>{h}") for h in heads]
    check("A section order", pos == sorted(pos) and -1 not in pos, True)
    for h in ("Errors", "Tool usage", "Files", "Activity feed"):
        check(f"A {h} collapsed", f'<details class="diag"><summary><h2>{h}' in html, True)
    check("A UC in header", "UC-007" in html[:html.find("<h2>")], True)


def test_fallbacks(root):
    path, _ = build_pipeline(root / "B", with_meta=False, with_markers=False, extra_gate=True)
    data = sr.analyze_session(path)
    r = runs_by_id(data)
    check("B linked by prompt", r["toolu_A1"].get("linked_by"), "prompt")
    check("B prompt note", any("linked by prompt" in n for n in data["notes"]), True)
    check("B marker note", any("marker" in n for n in data["notes"]), True)
    check("B fix run still split", tool_calls(r["toolu_S1"]), 12)
    b3 = r["toolu_B3"]
    check("B inferred verdict", (b3["verdict"], b3["verdict_source"]), ("REQUEST CHANGES", "inferred"))
    check("B no findings from inferred run", [x for x in data["findings"] if x["run"] == "toolu_B3"], [])
    check("B rejection with no fix is not a loop", [lp["gate"] for lp in data["fix_loops"]], ["qa"])


def test_no_agents(root):
    path, proj = build_no_agents(root / "C")
    data = sr.analyze_session(path, project_root=proj)
    ctx = data["ctx"]
    check("C cat counted", ctx["per_file"].get("standards/testing.md", {}).get("reads"), 1)
    check("C head counted", ctx["per_file"].get("domain/glossary.md", {}).get("reads"), 1)
    check("C never read", ctx["never_read"], ["domain/overview.md"])
    files = set(data["files_all"])
    check("C no internal files", [p for p in files if "tool-results" in p], [])
    check("C relative path", "src/app.ts" in files, True)
    t = data["time"]
    check("C human wait", t["human_wait_s"], 600.0)
    check("C agents time", t["agents_s"], 0.0)
    check("C orchestrator", t["orchestrator_s"], 30.0)
    out = root / "C" / "out" / "sessC.report.html"
    summary = sr.write_outputs(data, path.name, out, compact=False)
    check("C empty runs", (summary["agents"], summary["runs"], summary["fix_loops"]), ({}, [], []))
    check("C orchestrator model", summary["orchestrator"]["model"], "claude-opus-5-5")


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for test in (test_pipeline, test_fallbacks, test_no_agents):
            try:
                test(root)
            except Exception as e:  # noqa: BLE001 - report and keep going
                FAILS.append(f"{test.__name__}: {type(e).__name__}: {e}")
    if FAILS:
        print("\n".join(f"✗ {f}" for f in FAILS))
        sys.exit(1)
    print("✓ session-report self-test passed")


if __name__ == "__main__":
    main()
