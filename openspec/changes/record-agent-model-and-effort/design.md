## Context

See proposal.md for the motivation. Here's where things stand today:

- `session_report.py` already reads the main transcript and each `subagents/agent-<id>.jsonl`. It
  works out each agent's model from `message.model` (`primary_model`) and shows it, shortened, in
  the per-agent value table (`render_value_table`). It already reads `version` (the Claude Code
  version) into the report header from the first line that has one.
- Transcripts also record effort on assistant lines, in two undocumented fields:
  `perTurnEffort` and `effort`. A sample of 60 recent subagent transcripts showed:

  | Agent | Model | `perTurnEffort` | `effort` |
  |---|---|---|---|
  | architect | claude-opus-5-5 | medium | medium |
  | junior-dev | claude-sonnet-5 | None | medium |
  | architect | claude-opus-4-8 | None | medium |
  | claude-code-guide | claude-haiku-4-5 | None | (absent) |

  Newer subagent transcripts carry only `perTurnEffort`.
- `build-use-case` step 7 runs the report at the end of every run and writes the retrospective
  itself. The orchestrator can't see a subagent's model directly. The transcript is the only
  reliable source.

## Goals / Non-Goals

**Goals:**
- One extractor: `session_report.py` is the only code that reads model, effort and version.
  The retrospective copies its output.
- Honest values: anything the transcript doesn't record is `unknown`.

**Non-Goals:**
- No hook changes. Hook payloads don't carry the model, and reading transcripts from a hook would
  duplicate the report.
- No pinning or enforcing models. This change records what ran; it doesn't change what runs.
- No backfilling earlier retrospectives.
- No per-turn effort timeline. One value (or list of values) per agent type is enough.

## Decisions

### 1. Effort resolution: `perTurnEffort`, then `effort`, then `unknown`
For each assistant message, take the first non-null value of `perTurnEffort` or `effort`. An
agent's effort is the set of values across its messages, joined with commas when there's more
than one. If there are no values, it's `unknown`.

- *Why this order:* `perTurnEffort` is the per-request value and is the only field in newer
  subagent transcripts. `effort` is the fallback for older transcripts.
- *Alternative considered:* use only `perTurnEffort`. Rejected: older transcripts would then show
  `unknown` even where `effort` is present.
- *Alternative considered:* fall back to the agent's frontmatter or the session's `/effort`
  setting. Rejected: that guesses, and an audit record must not guess.
- *Caveat, written into the docs:* we don't know whether `effort` on a subagent line is that
  agent's own setting or one inherited from the session. Values are "as recorded by Claude Code".

### 2. Full model IDs in the summary, short IDs in the HTML
The HTML keeps `short_model` (`opus-5-5`) to stay readable. The JSON summary and the
retrospective use full IDs (`claude-opus-5-5`), because an audit record should match the API's
identifiers exactly.

### 3. `--summary` replaces stdout with one JSON object
With `--summary`, the script writes the HTML report as usual, then prints a single JSON object
instead of its two status lines. Without the flag, stdout is unchanged.

- *Alternative considered:* a sidecar `<session>.summary.json`. Rejected: it's one more file to
  commit, and the retrospective already holds the durable copy.
- *Alternative considered:* print the JSON after the status lines. Rejected: the orchestrator
  would have to find the JSON in mixed output.

Shape:
```json
{
  "session": "3abb03dd-…",
  "report": "reports/sessions/3abb03dd-….report.html",
  "claude_code": "2.1.288",
  "orchestrator": {"model": "claude-opus-5-5", "effort": "medium"},
  "agents": {
    "architect":  {"model": "claude-opus-5-5", "effort": "medium", "runs": 1},
    "junior-dev": {"model": "claude-sonnet-5, claude-opus-5-5", "effort": "unknown", "runs": 2}
  }
}
```
The orchestrator's values come from the main transcript's assistant messages. They use the same
rules as an agent's.

### 4. Retrospective front matter uses YAML flow maps
```yaml
claude_code: 2.1.288
orchestrator: {model: claude-opus-5-5, effort: medium}
agents:
  architect:  {model: claude-opus-5-5, effort: medium, runs: 1}
  junior-dev: {model: "claude-sonnet-5, claude-opus-5-5", effort: unknown, runs: 2}
```
There's one line per agent, so it's easy to grep (`grep -h 'junior-dev:' retrospectives/*.md`)
and to read in a diff. It sits after `agent_runs` in the template.

### 5. Prompt change in `build-use-case` step 7
Current wording (the *Session report* bullet):

> **Session report:** find this session's log with `ls -t ~/.claude/projects/$(pwd | sed 's#[/.]#-#g')/*.jsonl | head -1` and generate its report with `python3 "${CLAUDE_PLUGIN_ROOT}/skills/session-report/session_report.py" <log> --compact` (it writes to the profile's session-reports path). Put the session id and report path in the front matter.

Replacement:

> **Session report:** find this session's log with `ls -t ~/.claude/projects/$(pwd | sed 's#[/.]#-#g')/*.jsonl | head -1` and generate its report with `python3 "${CLAUDE_PLUGIN_ROOT}/skills/session-report/session_report.py" <log> --compact --summary` (it writes to the profile's session-reports path). It prints one JSON object: copy its `session`, `report`, `claude_code`, `orchestrator` and `agents` into the front matter exactly as given (quote a comma-separated value), even if the project's template lacks those fields. Never fill them from agent frontmatter. If the script fails, set them to `unknown` and say so in the Summary.

This fixes a gap, not a past failure. No retrospective has recorded models so far, and the
model-mix seen in recent transcripts (see Context) was only discovered by digging through raw
transcripts.

### Stack-agnostic and OpenSpec boundaries
The fields describe Claude Code, not the host project's stack, so nothing in the change names a
language or tool. OpenSpec's artifacts and procedures are untouched. This change is about the
plugin's own run records.

## Risks / Trade-offs

- [Effort fields are undocumented and may be renamed or dropped in a future Claude Code release]
  → The script reads them defensively and falls back to `unknown`. The docs say values are "as
  recorded", and a run where every value is `unknown` is easy to spot.
- [`effort` on subagent lines may be the session's setting, not the agent's] → Prefer
  `perTurnEffort`, and document the caveat. An audit reader then knows the confidence level.
- [The orchestrator may copy the JSON loosely, e.g. shortening IDs or filling gaps] → Step 7 says
  "exactly as given" and "never from frontmatter". The `run-retrospective` spec scenarios are the
  manual check.
- [Matching agents to transcripts by prompt (`link_subagents`) can miss a run, leaving its model
  as `None`] → Such a run reports `unknown` instead of disappearing. This is existing behaviour
  and isn't changed here.

## Migration Plan

No migration. Earlier retrospectives keep their current front matter. Host projects with a copied
`TEMPLATE.md` can add the three fields to it, which is optional because the orchestrator adds
them anyway. To roll back, revert the change. Retrospectives that already have the extra front
matter stay valid YAML.

## Open Questions

- Does subagent `effort` reflect the agent's own setting? A controlled run would answer it: an
  agent with `effort: high` in its frontmatter, launched from a `medium` session. The answer only
  changes the caveat in the docs, not the approach.
