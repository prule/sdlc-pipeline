---
name: session-report
description: Turn a Claude Code session log (.jsonl) into a self-contained HTML report — an agent timeline (Gantt), a subagent value/efficiency table, which review gates caught issues, an errors & friction panel, context-doc ingestion, and a filterable activity feed. Use when the user wants to analyse a session, see what agents ran when and how long they took, review pipeline efficiency, compare two runs, or find where things went wrong.
allowed-tools: Bash(python3:*), Bash(ls:*), Read, Glob
license: MIT
---

Generate an HTML report from a Claude Code session log so a human can see, at a
glance, what happened in a run: which agents ran, when, for how long, what they
decided, where errors occurred, and whether the review gates earned their place.

The generator is `${CLAUDE_PLUGIN_ROOT}/skills/session-report/session_report.py`
(Python 3.8+, standard library only).

## When to use

- "Analyse / visualise this session", "what agents ran", "how long did the
  pipeline take", "where did it go wrong", "did the reviewers catch anything",
  "are the subagents actually useful", "compare these two runs".

## Input

A session log path. Logs live under
`~/.claude/projects/<slug>/<session-id>.jsonl`, where the slug is the project's
absolute path with `/` and `.` replaced by `-`. If the user doesn't give a path,
list recent logs and ask which one (newest is usually the one they mean — and
the newest is the current session):

```bash
ls -lt ~/.claude/projects/$(pwd | sed 's#[/.]#-#g')/*.jsonl | head
```

## Steps

1. Run the generator from the project root. **Always pass `--compact`** —
   pipeline runs span hours or days with long idle gaps, and compact collapses
   the dead air so short agent runs stay visible. Reports default into
   `reports/sessions/` in the project so they're versioned alongside the code.
   If `.claude/sdlc-profile.md` names a different session-reports path, pass it
   as `--out-dir`; if it names different domain/standards paths, pass them as
   `--context-dirs <a>,<b>`.

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/skills/session-report/session_report.py" <log.jsonl> --compact
   ```

   This writes `reports/sessions/<session-id>.report.html` and prints a one-line
   summary (events, agent runs, issues caught, errors). If the user wants the
   models, effort and Claude Code version as data, add `--summary`: it prints
   one JSON object instead (shape in the README).

2. Give the user the report path (offer `--open` to open it in a browser) and
   relay the printed summary line. Reports are meant to be committed with the
   change they describe.

3. If the user is drawing conclusions about pipeline efficiency, point them at
   the **Insights**, **Subagent value & efficiency**, and **Review-gate value**
   sections — those are the ones built to show whether each subagent is pulling
   its weight.

## Measuring whether domain & standards context helps

If the user asks whether the curated domain and standards docs are being
read / are helping or hindering:

- The **Context ingestion** panel already answers "are they read and used?" —
  per-doc reads, informed reads (before first write), citations, influence
  score, never-read / read-but-never-cited flags, reviewer catches attributed to
  the doc they cite, and a **Value/1K** (influence per 1000 tokens) signal-density
  score that flags large-but-rarely-used docs as `wordy / low-signal?`. The
  **Subagent value** table also shows **which model and effort** each agent ran. Point them
  there first.
- "Helping vs hindering" is a causal question that needs a counterfactual, not a
  single run. Recommend an **ablation**: run the same use case with vs without
  (or with trimmed) context, then diff the two runs:

  ```bash
  python3 "${CLAUDE_PLUGIN_ROOT}/skills/session-report/session_report.py" <full>.jsonl \
      --compare <stripped>.jsonl --label-a "full" --label-b "stripped"
  ```

  This writes a `compare-…report.html` diffing outcome metrics (issues caught,
  errors, rework, tool calls, output tokens = cost, context reads/catches).
  Don't claim causation from one run's reads alone.

## Notes / gotchas

- **Subagents are included by default.** Each subagent has its own transcript at
  `<session-id>/subagents/agent-<id>.jsonl`; the script reads them all, folds
  their tool/file activity into the Tool-usage and Files-touched panels, and adds
  per-subagent workload columns (inner tool calls, files, output tokens) to the
  value table. Matched to parent Agent calls by prompt. Pass `--no-subagents`
  for top-level only.
- **Namespaced agents.** Plugin agents appear as `sdlc-pipeline:<name>`; gates
  are matched on the short name, so runs from before and after the plugin
  compare cleanly.
- **Background agents** (`run_in_background: true`) return an instant
  "launched" stub; their real duration and output arrive later in a
  `<task-notification>`. The script correlates the two by tool-use-id, so async
  agents are timed correctly — don't "fix" the near-instant stub yourself.
- **Resumes & hand-backs:** a `SendMessage` to an already-spawned agent, such as
  an architect revision or a spec re-review, counts as another run of that
  subagent. A run's result is its `[Subagent hand-back]` peer message when there
  is one, because the notification then holds only a pointer. So correction
  loops appear in the run counts and in the gate verdicts.
- **Verdict detection is heuristic** — it keys off formal tokens
  (`REQUEST CHANGES`, `NOT READY`, uppercase `CRITICAL`/`FAIL`, ❌) with a
  "no/0 critical" guard. An approving gate that fixed or logged something
  shows as `FIXED IN PLACE` or `DEFECT LOGGED`, and counts as a catch. It's
  good, not perfect; the on-screen snippet lets the reader verify. A couple of
  runs may show verdict `—` when unclassifiable.
- Full documentation and the report anatomy: `README.md` beside this file.
