## Why

Agent frontmatter says `model: opus`, but that doesn't record what actually ran. In recent runs,
agents with that setting ran on `claude-sonnet-5`, `claude-opus-5-5` and `claude-opus-4-8`. The
alias also moves silently when a new Opus ships. The session transcripts hold the real model,
effort and Claude Code version, but Claude Code deletes old transcripts. The pipeline promises an
audit trail, so these facts belong in the files a run commits: the session report and the
retrospective.

## What Changes

- **Session report** shows each agent's effort level next to its model, and the Claude Code
  version the session ran on. Values the transcript doesn't record show as `unknown`, never a
  guess.
- **Session report** gains a `--summary` option. With it, the script prints one JSON object to
  stdout: session id, report path, Claude Code version, the orchestrator's model and effort, and
  each agent type's model, effort and run count. The HTML report is still written.
- **Retrospective** front matter gains `claude_code`, `orchestrator` and an `agents` block
  (model, effort and runs per agent type). The template documents them.
- **`build-use-case`** step 7 runs the session report with `--summary` and copies the result into
  the retrospective's front matter. It adds these fields even when the project's own
  retrospective template predates them.
- **Docs**: `docs/observability.md`, `docs/evaluating-the-pipeline.md` and the session-report
  README describe the new fields and their limits.

## Capabilities

### New Capabilities
- `session-report`: what the session report records about the models, effort and Claude Code
  version a run used, and the machine-readable summary it can emit.
- `run-retrospective`: the run facts the retrospective's front matter records, including the
  model and effort each agent ran.

### Modified Capabilities
None. The repo has no specs yet.

## Impact

- **Changes:** `skills/session-report/session_report.py`, `skills/session-report/SKILL.md` and
  `README.md`, `skills/build-use-case/SKILL.md`, `templates/retrospective.md`,
  `docs/observability.md`, `docs/evaluating-the-pipeline.md`, `CHANGELOG.md`, both manifests.
- **Unchanged:** agents, hooks and `scripts/pipeline-report.py`.
- **Host projects:** nothing to do. The orchestrator adds the new front-matter fields even if a
  project's `retrospectives/TEMPLATE.md` lacks them. Projects that copied the template can add the
  fields to their copy if they want them documented there. Earlier retrospectives stay as they are.
- **Dependencies:** none. The script stays standard-library Python 3.8+.
- **Version:** 0.1.0 → 0.2.0. It's a new feature with new output. Nothing breaks and no host
  project has to change its profile, but a minor bump marks the new retrospective fields.
