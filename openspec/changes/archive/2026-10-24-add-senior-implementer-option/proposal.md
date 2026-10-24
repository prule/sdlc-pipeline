# Proposal

## Why

Every run implements with `junior-dev`, then has `senior-dev` review and fix the diff. When the
senior dev keeps fixing the same kinds of junior mistakes, or the qa↔junior-dev loop runs twice,
the round-trips cost more time than a stronger first pass would. Teams want a switch that lets
the senior dev do the implementing, and lets them turn the junior dev back on when they want it.

## What Changes

- New profile setting **Implementer** (`junior-dev` | `senior-dev`) in a new `## Pipeline` section
  of `.claude/sdlc-profile.md`. If the setting or section is missing, the implementer is
  `junior-dev`, so the pipeline works as it does today.
- `build-use-case` takes a per-run override, `--senior` or `--junior`, before the use case. The flag
  wins over the profile for that run only.
- When the implementer is `senior-dev`, the orchestrator spawns `senior-dev` for stage 3
  (implement). QA defects go back to that same senior-dev run. Stage 5 (code review) stays: the
  orchestrator spawns a **fresh** `senior-dev` run that has not seen the implementation, so the
  review is still independent.
- Gate 1 shows which implementer will run and where that choice came from (profile, flag or
  default), so the human can change it before implementation starts.
- `senior-dev` gets an implement mode. It follows the same implement procedure as `junior-dev`
  (profile, `opsx:apply`, Verify) and keeps the same rule: stop on a plan defect, don't redesign.
  It gains the `Skill` tool so it can invoke `opsx:apply`.
- The retrospective front matter records `implementer: junior-dev | senior-dev`.
- The session report treats a senior-dev implement run as a builder run, not a gate, so its
  verdicts, findings and QA fix loops come out right.
- Docs: `docs/pipeline.md`, `docs/profile.md`, `README.md`, `CHANGELOG.md`.

## Capabilities

### New Capabilities
- `implementer-choice`: how a host project and a single run choose which agent implements the
  approved plan, and how the pipeline behaves under each choice.

### Modified Capabilities
- `run-retrospective`: the retrospective records which agent implemented the change.
- `session-report`: a senior-dev implement run is not counted as a gate run.

## Impact

- **Agents:** `agents/senior-dev.md` (implement mode, `Skill` tool), `agents/junior-dev.md`
  (description only, if it needs to say it is the default implementer).
- **Skills:** `skills/build-use-case/SKILL.md` (resolve implementer, stage 3 and 4 routing, Gate 1,
  retrospective field); `skills/session-report/session_report.py` and `selftest.py`. `init`
  needs no change: it copies the profile template, so new profiles get the section.
- **Templates:** `templates/sdlc-profile.md` (new `## Pipeline` section),
  `templates/retrospective.md` (`implementer` field).
- **Docs:** `README.md`, `docs/pipeline.md`, `docs/profile.md`, `CHANGELOG.md`.
- **Manifests:** `plugin.json` and `marketplace.json` to 0.7.0.
- **Host projects:** nothing is required. Existing profiles have no `## Pipeline` section, so they
  keep the junior dev. To make the senior dev the project default, add the section to the
  profile. To use it for one run, pass `--senior`.
- **Semver:** minor bump (0.6.0 → 0.7.0). It adds an optional profile setting and a new pipeline
  mode. Nothing a host project already has stops working.
