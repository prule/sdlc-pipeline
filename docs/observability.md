# Observability

Three tools answer three questions about a run:

| Tool | Answers | Output |
|------|---------|--------|
| Event-log hooks | What did this run touch? | `logs/pipeline-events.jsonl`, `logs/pipeline-report.html` |
| Session report | Did each agent, gate and context doc earn its place? | `reports/sessions/<session>.report.html` |
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
for sessions recorded before the plugin was installed. It shows an agent Gantt timeline, a per-agent
value and efficiency table (including the model each agent ran), every review gate's verdict and what
it caught, errors and friction, tools and files, and how the domain and standards docs were read and
cited.

`/sdlc-pipeline:build-use-case` generates one at the end of every run. For any other session, ask
*"analyse this session"*. Full reference: [skills/session-report/README.md](../skills/session-report/README.md).
To use reports to judge a change to the pipeline, see [evaluating-the-pipeline.md](evaluating-the-pipeline.md).
