## Why

The session report is the main tool for tuning the pipeline, but parts of it are wrong. On the
logbook UC-0.1 run it reported the standards docs as "never read" while also crediting them with six
reviewer catches. It credited all of a resumed agent's work to the agent's first run, so 6 of 11 runs
showed no work and every fix loop looked free. It also guessed gate verdicts from keywords and showed
the middle of an answer as the snippet, even though the agents write structured findings. A tuner
can't trust a report like that, and a future trends report built on these numbers would spread the
errors.

## What Changes

- **Exact subagent linking.** Each subagent transcript is linked to its Agent call through the
  `toolUseId` in its `agent-<id>.meta.json`. Prompt matching remains only as a fallback, and the report
  says when it was used.
- **Per-run work.** A resumed agent's transcript is split at each resume, so every run, resumed or
  not, shows its own tool calls, tokens, files and duration.
- **Shell file access counted.** Reads and writes made through common shell commands count in the
  context and files panels, labelled "incl. shell". Claude Code's internal files are left out, and
  paths are shown relative to the project.
- **Parsed findings.** The report reads each gate's **Run-log findings** block (`P1`, `Q1`, `C1` with
  kind, severity, rule and status) into a findings table. Keyword verdicts remain the fallback for
  runs with no block.
- **New measures for tuning:** fix loops (which findings started each loop, what the fix and
  re-check cost), a time breakdown (agents working, waiting on the human, orchestrator), and tokens
  per run and per agent type (input, cache write, cache read, output). Tokens only, no prices.
- **Summary file.** Every report run also writes `<session>.summary.json` beside the HTML. It holds
  the existing `--summary` fields plus the new measures, so a later trends report can work from
  summary files alone. `--summary` prints the same object.
- **Layout.** The report is reordered for tuning: outcome and totals, the run as a swimlane with
  fix loops marked, findings, agents, context. Errors, tools, files and the activity feed move into
  collapsed sections.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `session-report`: adds requirements for exact linking, per-run work, shell file access, parsed
  findings, fix loops, the time breakdown, token detail, the summary file and the layout. The
  machine-readable summary requirement changes: the object gains new fields and is also written to
  a file.

## Impact

- **Components:** the session-report skill (`session_report.py`, `SKILL.md`, `README.md`, a new
  self-test with synthetic transcripts), `build-use-case` (one line: the commit reminder names the
  summary file), `scripts/validate.py` (runs the self-test), docs (`docs/observability.md`, the
  README's quick start), manifests and `CHANGELOG.md`. No agent prompt changes; the findings format
  the report parses already exists in the agents.
- **Host projects:** need do nothing. Reports gain a `.summary.json` file beside each HTML report,
  which should be committed with it. `build-use-case` keeps working: every field it copies into the
  retrospective is unchanged. Reports generated before this change are not regenerated.
- **Compatibility:** older transcripts without `meta.json` files or resume markers still produce a
  report, using today's behaviour for the missing parts.
- **Semver:** minor bump to 0.5.0. It adds new report content and a new output file, and changes no
  existing field.
