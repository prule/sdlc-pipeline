# Observability

Three tools answer three questions about a run:

| Tool | Answers | Output |
|------|---------|--------|
| Event-log hooks | What did this run touch? | `logs/pipeline-events.jsonl`, `logs/pipeline-report.html` |
| Session report | Did each agent, gate and context doc earn its place? | `reports/sessions/<session>.report.html`, `<session>.summary.json` |
| Retrospectives | What keeps going wrong, and what should change? | `retrospectives/<date>-<change>.md` (see [pipeline.md](pipeline.md#retrospectives)) |

For cost and token trends over many runs, Claude Code's built-in OpenTelemetry export works alongside
these. See the [monitoring docs](https://code.claude.com/docs/en/monitoring-usage).

## Event-log hooks

While the plugin is enabled, [`hooks/hooks.json`](../hooks/hooks.json) runs
[`hooks/log-event.py`](../hooks/log-event.py) on `PreToolUse`, `PostToolUse`, `SubagentStop`,
`UserPromptSubmit`, `SessionStart` and `Stop`. Each event becomes one compact line in
`<project>/logs/pipeline-events.jsonl`: time, event, tool, session, and the meaningful part of the
tool input (file path, command, skill, subagent type, description), cut to 300 characters. Full
payloads are never stored.

The hook always exits 0 and swallows its own errors, so it can't block or break a session. It needs
`python3` on the `PATH`. Add `logs/` to `.gitignore` (`/sdlc-pipeline:init` does).

Render the log as a dashboard of agents spawned, tool counts, skills used, files read and written,
and a filterable timeline:

```bash
python3 <plugin>/scripts/pipeline-report.py      # → logs/pipeline-report.html
: > logs/pipeline-events.jsonl                   # start a fresh baseline
```

`<plugin>` is your clone of this repo, or the installed copy under `~/.claude/plugins/`.

## Session report

The `session-report` skill reads the session transcript itself, not the hook log, so it also works
for sessions recorded before the plugin was installed. It leads with the run's use case, change and
totals: wall time split into agents working, waiting on you and the orchestrator, fix loops, findings
and tokens. Then a timeline with one lane per agent, your waits and each fix loop; every gate run's
verdict and every finding it recorded, with the cost of each fix loop; a per-agent and per-run table
(model, effort, tool calls, tokens); and how the domain and standards docs were read and cited.
Errors, tools, files and the activity feed are collapsed below. The header shows the Claude Code
version.

Each report also writes `<session>.summary.json` beside it: the same facts as data, for comparing
runs over time. Commit it with the report.

`/sdlc-pipeline:build-use-case` generates one at the end of every run. It runs the report with
`--summary`, which prints the summary file's JSON, and copies the Claude Code version and each
agent's model, effort and run count into the retrospective's front matter. Transcripts in `~/.claude` are
eventually deleted, so the committed retrospective is the lasting record of what ran.

Model and effort are as recorded by Claude Code. The model is the full ID from each message, which
can differ from an agent's `model: opus` alias. Effort comes from undocumented transcript fields
(`perTurnEffort`, then `effort`). It shows `unknown` where nothing was recorded, for example on older
Claude Code versions or models without effort levels. On a subagent it may reflect the session's
setting rather than the agent's own. For any other session, ask
*"analyse this session"*. Full reference: [skills/session-report/README.md](../skills/session-report/README.md).
To use reports to judge a change to the pipeline, see [evaluating-the-pipeline.md](evaluating-the-pipeline.md).
