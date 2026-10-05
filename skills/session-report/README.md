# Session Report

Turn a **Claude Code session log** (`.jsonl`) into a single, self-contained HTML
report so you can *see* what happened in a run — especially in the multi-agent
SDLC pipeline (`architect → spec-reviewer → junior-dev → qa → senior-dev`) that
the [sdlc-pipeline](../../README.md) plugin runs.

It answers, at a glance:

- **What agents ran, when, and for how long** — a Gantt timeline.
- **Are the subagents pulling their weight?** — a value/efficiency table and
  auto-generated insights.
- **Where did the review gates earn their place?** — every reviewer run with its
  verdict and a snippet of what it caught.
- **What went wrong?** — failed commands, rejected tool calls, failed agents.
- **What decisions were made?** — a filterable, chronological activity feed.
- **What was touched?** — tools used (with time and errors) and every file read/written/edited.

This is a Claude Code [skill](https://code.claude.com/docs/en/skills) in the
`sdlc-pipeline` plugin: Claude picks it up automatically when you ask to analyse a
session, and `/sdlc-pipeline:build-use-case` runs it at the end of every pipeline
run. You can also run the script directly.

## Quick start

Run these from the project root. `SR` is this folder — in a clone of the plugin
repo it is `<clone>/skills/session-report`; an installed plugin lives under
`~/.claude/plugins/`.

```bash
# 1. Find the session log you want (newest first)
ls -lt ~/.claude/projects/$(pwd | sed 's#[/.]#-#g')/*.jsonl | head

# 2. Generate the report (collapses idle gaps so short runs stay visible)
python3 "$SR/session_report.py" \
    ~/.claude/projects/$(pwd | sed 's#[/.]#-#g')/<session-id>.jsonl \
    --compact --open
```

The report is written to **`reports/sessions/<session-id>.report.html`** inside
the project, so it's versioned alongside the code it describes. Open it in any
browser — no server, no dependencies.

Or just ask Claude: *"analyse this session log"* / *"did the reviewers catch
anything in that run?"*

### Where are the logs?

Claude Code stores one `.jsonl` per session under
`~/.claude/projects/<slugified-project-path>/`, where the slug is the project's
absolute path with every `/` and `.` replaced by `-` (`$(pwd | sed 's#[/.]#-#g')`).
For `/Users/me/work/shop` the folder is `~/.claude/projects/-Users-me-work-shop/`.

## Usage

```
python3 session_report.py <session.jsonl> [-o OUTPUT] [--out-dir DIR]
                          [--context-dirs DIRS] [--compact] [--open] [--summary]

  <session.jsonl>   Path to the session log.
  -o, --output      Output HTML path. Default: <out-dir>/<name>.report.html
  --out-dir         Report folder, relative to the current directory.
                    Default: reports/sessions
  --context-dirs    Comma-separated folders whose *.md docs count as curated
                    context in the Context-ingestion panel. Default:
                    domain,standards
  --compact         Collapse idle gaps in the agent timeline (recommended —
                    runs span hours/days, so absolute-time bars become slivers).
  --no-subagents    Report the top-level session only (skip subagent transcripts).
  --compare OTHER   A/B-compare two runs on outcome metrics (SESSION is A,
                    OTHER is B). See "Measuring whether domain & standards help".
  --label-a/-b      Labels for the two runs in a --compare report.
  --open            Open the finished report in your browser.
  --summary         Print the run summary (the same JSON written to
                    <session>.summary.json) instead of the status lines.
                    build-use-case uses it to fill the retrospective's front
                    matter.
```

Every run writes two files: `<session>.report.html` and `<session>.summary.json`
beside it. Commit both with the change they describe.

No third-party packages — Python 3.8+ standard library only.

### The summary file

`<session>.summary.json` holds the facts a retrospective records and a later trends
report reads, so old transcripts never need re-parsing. `--summary` prints the same
object. Abridged:

```json
{
  "schema": 1,
  "session": "47d3f4bc-…",
  "report": "reports/sessions/47d3f4bc-….report.html",
  "summary": "reports/sessions/47d3f4bc-….summary.json",
  "claude_code": "2.1.289",
  "use_case": "UC-0.1", "change": "uc-0-1-open-logbook",
  "orchestrator": {"model": "claude-opus-5-5", "effort": "medium", "tokens": {"…": 0}},
  "agents": {
    "qa": {"model": "claude-opus-5-5", "effort": "medium", "runs": 2,
           "duration_s": 486.6, "tool_calls": 33,
           "tokens": {"input": 146, "cache_write": 236569, "cache_read": 4851961, "output": 735}}
  },
  "time":   {"wall_s": 3729.4, "agents_s": 2050.0, "human_wait_s": 1148.3, "orchestrator_s": 531.1},
  "tokens": {"input": 846, "cache_write": 1415581, "cache_read": 29865726, "output": 86233},
  "runs": [{"id": "toolu_…", "agent": "qa", "description": "Verify UC-0.1 implementation",
            "start": "2026-10-05T02:01:45Z", "duration_s": 433.0, "resumed": false,
            "linked_by": "id", "tool_calls": 29, "tokens": {"…": 0},
            "verdict": "handed-back", "verdict_source": "findings", "findings": ["Q1", "…"]}],
  "findings": [{"id": "Q1", "gate": "qa", "run": "toolu_…", "kind": "test-gap",
                "severity": "medium", "rule": "standards/testing.md §1", "where": "…",
                "status": "handed-back", "root_cause": "…", "recommendation": "…"}],
  "fix_loops": [{"gate": "qa", "started_by": "toolu_…", "findings": ["Q1", "Q2"],
                 "fix_runs": ["toolu_…"], "recheck_run": "toolu_…",
                 "duration_s": 257.5, "tool_calls": 12, "tokens": {"…": 0}}],
  "notes": []
}
```

- `schema` goes up when a field changes meaning, so a trends report can tell
  formats apart.
- `session`, `report`, `claude_code`, `orchestrator.model`/`effort` and
  `agents.<type>.model`/`effort`/`runs` are the fields `build-use-case` copies into
  the retrospective. Models are full IDs; `agents` is keyed by agent type without
  the plugin namespace. A value that differs across runs is a comma-separated
  list, and `claude_code` is a list when the session spans several versions.
  Anything the transcript didn't record is `unknown`.
- Tokens are counts only, never prices.
- `findings` has one entry per finding per gate run, so a finding a re-check
  confirms as fixed appears twice, with each run's status.
- `notes` lists any fallbacks the analysis used (see "How it works").
- A session that spawned no agents has `"agents": {}` and empty `runs` and
  `fix_loops`.

## What's in the report

The report is ordered for tuning the pipeline: outcome and totals first, then the
run, then the evidence. Diagnostics are collapsed until you open them.

| Section | What it tells you |
|---|---|
| **Header and cards** | The use case and change (when the session names them). Wall time split into agents working, waiting on you and the orchestrator; agent runs and how many were resumed; fix loops and their rework time; distinct findings by severity; output and input tokens (with cache share); errors. |
| **Notes** | Any fallback the analysis used, such as runs linked by prompt or resume markers that didn't match. Absent when there were none. |
| **Insights** | Which gates caught something, what their fix loops cost, where errors clustered, the slowest run. |
| **Timeline** | One lane per agent type; resumed runs share their agent's lane (dark left edge). A **you** lane shows waits on the human; a **fix loops** lane brackets each loop from the gate run to its re-check. Green outline = caught something; red = failed; hatched = pending. Hover a bar for its tool calls and tokens. With `--compact`, idle gaps are collapsed but widths stay proportional. |
| **Findings** | **Gate runs**: every gate run with its verdict, whether the verdict came from its findings block or was inferred from keywords, and its summary line. **Findings**: one row per finding, with severity, kind, the rule it cites, and its status in each gate run that mentioned it (for example `handed-back` then `fixed-by-rework`); hover for where it was and the recommendation. **Fix loops**: what each gate sent back, the run that fixed it, the run that re-checked it, and the cost. |
| **Agents** | Per agent type: model, effort (as recorded; `unknown` if not), runs, time, tool calls, files, input, cache-write, cache-read and output tokens, gate catch rate, errors. **Every run** (expandable) lists each run with its own cost. |
| **Context** | Whether the curated docs (`domain/` and `standards/` by default, see `--context-dirs`) reach the agents; see below. |
| **Errors & friction** *(collapsed)* | Failed commands, failed agents, and tool calls you rejected. |
| **Tool usage** *(collapsed)* | Every tool called, top-level and inside subagents, with count, time and errors. |
| **Files touched** *(collapsed)* | Every project file read, written or edited across the run, including through shell commands, relative to the project root. Claude Code's own files (tool results, transcripts, the scratchpad) are left out. |
| **Activity feed** *(collapsed)* | Chronological, filterable stream: prompts, decisions, tool calls, agent results, thinking. |

## Subagents are included

The multi-agent pipeline does most of its real work *inside* subagents
(`architect`, `junior-dev`, `qa`, …), and each gets its own full transcript at
`~/.claude/projects/<slug>/<session-id>/subagents/agent-<id>.jsonl`. The script
reads those too and folds them in:

- **Tool usage** and **Files touched** aggregate the top-level session *plus*
  every subagent — so you see all files read/written/edited across the run, not
  just the handful the orchestrator touched directly (e.g. 335 files instead of
  67 in one sample run).
- The **Agents** table gains per-agent columns (**Tool calls**, **Files** and the
  four token counts), so you can see who did the heavy lifting (typically
  `junior-dev`) versus the lighter review gates. **Every run** breaks that down
  per run, including resumed fix runs.

Each transcript is matched to the Agent call that started it through the
`toolUseId` in the `agent-<id>.meta.json` Claude Code writes beside it. Older
sessions without meta files fall back to matching the prompt, and the report says
how many runs were linked that way. Pass `--no-subagents` to report the top-level
session only.

Plugin agents are namespaced (`sdlc-pipeline:qa`). The report shows the full
name and matches review gates on the short name, so `qa` and
`sdlc-pipeline:qa` both count as the QA gate.

## Measuring whether `domain/` & `standards/` help

A recurring question with the multi-agent pipeline: *is the context we curate in
`domain/` and `standards/` actually being used, and is it helping or hindering?*
That splits into three layers — the report measures the first two; `--compare`
handles the third.

**1. Ingestion — are they read?** The **Context ingestion** panel lists every
`domain/*` and `standards/*` doc with:
- **Reads** — how many times agents opened it (across all subagents), with the
  Read tool or common shell commands (`cat`, `head`, `tail`, `sed`, `grep`);
- **Informed** — the share of those reads that happened *before* the agent's
  first write (i.e. the doc could actually shape the output, vs. being opened
  after the fact);
- **Cited** — how often the agent's own reasoning text references the doc;
- **Influence** = reads + citations, and which agent types read it;
- flags for docs **never read** (dead weight) and **read but never cited**.

**2. Attribution — did they help catch anything?** When a review gate's verdict
explicitly names a doc (e.g. a `REQUEST CHANGES` citing `clean-architecture.md`),
that catch is attributed to the doc — direct evidence it earned its place.

**Is a doc too wordy / bloated?** Each doc also shows its **size** (approx
tokens), **read cost** (reads × size = context tokens spent re-reading it), and
**Value/1K** — influence per 1000 tokens of the doc, i.e. *value per word*. A
large doc with low Value/1K is flagged `wordy / low-signal?`; a lean, heavily-used
doc is flagged `dense`. This is a **signal-density proxy**, not proof: it tells you
*where* to look. Confirm by trimming the doc and re-running with `--compare` to
see if outcomes hold. (It can't tell you *which paragraphs* are noise — for that,
trim and compare, or have an LLM rate each section's actionability.)

**3. Effect on outcome — help or hinder?** Reading ≠ benefit. Proving effect
needs a **counterfactual**: run the *same* use case twice, once with the context and
once without (or trimmed), and diff the outcomes:

```bash
python3 "$SR/session_report.py" \
    <full-context-run>.jsonl \
    --compare <stripped-context-run>.jsonl \
    --label-a "full context" --label-b "stripped"
```

This writes `reports/sessions/compare-<a>-vs-<b>.report.html`: a metric-by-metric
diff (issues caught, errors, rejections, rework, tool calls, files, **output
tokens = cost**, context reads/catches). Green/red is applied only where the
direction is unambiguous (fewer errors/tokens = better; more doc-cited catches =
better); ambiguous metrics are shown without a verdict, because their meaning
depends on your hypothesis. To run the ablation: on a throwaway branch, strip
`domain/` + `standards/` (or a subset), re-run the use case, compare.

> Note: `CLAUDE.md` is always in every agent's context and is **not** counted as a
> read here — so a doc showing "never read" may still be reaching agents via the
> summary in `CLAUDE.md`.

## How it works (and its limits)

The parser reads the JSONL event stream and correlates each `tool_use` with its
matching `tool_result` (by `tool_use_id`) to compute durations and success.

Four details that matter for accuracy:

1. **Background agents.** Agents launched with `run_in_background: true` (e.g.
   `qa`, `senior-dev`) return an instant *"launched"* stub; their real duration
   and output arrive later in a `<task-notification>`. The script matches the
   notification back to the original launch, so async agents are timed by their
   real work, not by launch latency.
2. **Injected messages.** `<task-notification>`, `<system-reminder>` and other
   harness-injected user messages are filtered out of the "prompts" feed so they
   don't masquerade as things you typed.
3. **Resumed agents.** When the orchestrator sends a correction back to an agent
   it already spawned (`SendMessage` to that agent's id: an architect revision or
   a spec re-review), that counts as **another run** of the same subagent. The
   agent id is read from the spawn's result (`agentId: …`), or from `resumedAgentId`
   in the `SendMessage` result. A resume appends to the agent's first transcript,
   so the script splits that transcript by the runs' start times: each run gets
   the tool calls, tokens, files and time from its own slice. The "coordinator
   sent a message" line in the transcript is only a cross-check, because its
   wording is undocumented; if the counts differ, the report adds a note. If a
   resumed run has no start time, its agent's work stays on the first run, with a
   note.
4. **Hand-back reports.** A subagent can deliver its final report as a peer
   message (a user event with `origin.kind == "peer"` and a `[Subagent hand-back]`
   body). Its `<task-notification>` then carries only a pointer ("delivered to you
   as a message"). Each run is matched to the first hand-back from its agent id
   that arrives before that agent's next run. That report becomes the run's result
   (the text verdicts are read from), and the hand-back time becomes the run's end.

5. **Shell file access.** Bash commands are parsed for the common file forms:
   `cat`, `head`, `tail`, `less`, `wc`, `sed` (`-i` counts as a write), `grep`,
   `rg`, `>` and `>>` redirects, `tee`, `cp` and `mv`. Paths are resolved against
   the command's working directory; a `cd` inside the command, globs and variables
   are ignored. These counts are close estimates, labelled "incl. shell".

**Verdicts come from findings when they can.** Every gate ends its report with a
`## Run-log findings` block (`P1`, `Q1`, `C1`… with kind, severity, rule, where and
status). The script parses it: a run that handed any finding back is
`handed-back`; one that fixed something itself is `fixed-in-place`; otherwise it
is `clean`. Fix loops start at a `handed-back` run. The fixes are the following
resumed runs (or agents that already ran before the gate); a fresh agent of a new
type starts the next phase. The next run of the same gate is the re-check.

**Without a findings block, the verdict is inferred** and marked so. Whether a
review "caught something" is then guessed from the result text — formal tokens (`REQUEST CHANGES`, `NOT READY`),
uppercase severity labels (`CRITICAL`, `FAIL`, ❌), guarded against phrases like
"no CRITICAL issues" and adjectival "critically". An approving gate that still
found or fixed something also counts as a catch. **FIXED IN PLACE** means the
senior dev reported fixes ("I fixed", "Fixes applied", but not "Fixes applied:
none"). **DEFECT LOGGED** means QA passed the change but logged a defect. Issue
counts ignore HTTP status codes and section numbers ("404 problem", "§3 violation"). It's accurate on the reviewers'
structured output but can misread unusually-worded results; the on-screen snippet
lets you verify, and unclassifiable runs show a verdict of `—`.

## Files

- `session_report.py` — the generator (stdlib only).
- `selftest.py` — builds synthetic sessions in a temp folder and checks the
  analysis against the spec. `scripts/validate.py` runs it in CI.
- `SKILL.md` — the skill definition Claude loads.
- `README.md` — this file.
- Reports land in `reports/sessions/` under the directory you run it from (the
  project root), unless you pass `--out-dir` or `-o`.
