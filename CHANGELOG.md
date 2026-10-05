# Changelog

All notable changes to this plugin. Versions follow [semver](https://semver.org/); before 1.0, a
change that requires projects to edit their profile bumps the minor version.

## [0.6.0] — 2026-10-05

An MVP-first backlog of use cases, kept up to date as you build. Host projects need do nothing; run
`/sdlc-pipeline:plan-use-cases` once the PRD, domain and standards are in place.

### Added
- `/sdlc-pipeline:plan-use-cases`: reads the PRD and domain docs and writes `BACKLOG.md` at the
  project root. **MVP** holds the fewest use cases that let the primary actor reach the core goal
  end to end; **Increments** add value one use case at a time, most valuable first; **Later** keeps
  the rest. It asks *"Can the primary actor reach the core goal without this?"* of every MVP
  candidate. Re-runs keep ids and statuses, catch up work done outside the skills, and show a diff
  before writing.
- `templates/backlog.md`: the backlog's structure, the MVP-cut method and the entry format. Each
  entry is a checklist item (`B-<n>`), ticked when built; each section heading shows its built count.
- `docs/getting-started.md` step 6, "Plan the use cases".

### Changed
- `write-use-case` accepts a backlog entry (`B-3`, its title, or `next`) and links the saved use case
  from the entry. An idea with no entry is offered to the backlog, never added silently.
- `build-use-case` ticks the use case's backlog entry after the change is archived, and names the
  next entry. A run that stops before archive leaves `BACKLOG.md` unchanged.
- `init`, `write-domain` and `write-standards` suggest `plan-use-cases` before `write-use-case`.
- Nothing changes in a project without a `BACKLOG.md`.

## [0.5.0] — 2026-10-05

A session report you can trust for tuning the pipeline, and a summary file per run. Host projects
need do nothing; commit the new `<session>.summary.json` with each report.

### Added
- `<session>.summary.json` beside every session report: the existing `--summary` fields plus each
  run's cost, every gate finding, fix loops, the time breakdown and token counts (`schema: 1`).
  `--summary` prints the same object. A later trends report can work from these files alone.
- Report sections for tuning: gate runs and one row per finding with its status history, fix loops
  and what they cost, the time split between agents, waiting on you and the orchestrator, and
  input, cache-write, cache-read and output tokens per run, per agent and in total.
- `skills/session-report/selftest.py`: synthetic sessions that check the analysis. `validate.py`
  runs it.

### Changed
- Subagent transcripts are linked to their runs by tool-use id, with prompt matching only as a
  fallback the report notes.
- A resumed agent's work is credited to the resumed run, so fix runs show their real cost.
- Reads and writes through common shell commands (`cat`, `sed`, `grep`, redirects) count in the
  context and files panels. Claude Code's own files are left out, and paths are relative to the
  project. Docs that agents read with `cat` no longer show as "never read".
- Gate verdicts come from each gate's Run-log findings block; keyword verdicts are a marked
  fallback.
- The report leads with the use case, change and totals, then the timeline (one lane per agent,
  your waits, fix loops), findings, agents and context. Errors, tools, files and the activity feed
  are collapsed.
- `build-use-case` reminds you to commit the summary file with the report.

## [0.4.1] — 2026-10-05

Documentation of the order to set a project up in. Host projects need do nothing.

### Added
- `docs/getting-started.md`: set a project up in this order. Write a PRD with the `grill-me` skill,
  run `init`, `write-domain` and `write-standards`, then update `openspec/config.yaml` and the
  README to point at the new docs. It includes an example config and prompts for each step.

### Changed
- The README's prerequisites and Quick start follow that order. `docs/domain-and-standards.md`
  says to write the PRD first.
- `write-domain` reads the PRD before the other sources. The next step that `init`,
  `write-domain` and `write-standards` suggest follows the same order.

## [0.4.0] — 2026-10-05

An end-to-end testing template for the standards catalogue. Host projects need do nothing. To adopt
it, re-run `/sdlc-pipeline:write-standards` and pick `e2e-testing`.

### Added
- `templates/standards/concerns/e2e-testing.md`: three rules for any end-to-end suite (main flows
  only, locators by role or test id, a known starting state) and four for the Screenplay pattern
  (tests as the actor's goals, only Interactions touch the UI, assertions through Questions, tools
  through Abilities). The header defines the Screenplay terms. Tools are blanks the interview fills
  in, such as Playwright and Serenity/JS.

### Changed
- `scripts/validate.py` also rejects common end-to-end tool names in catalogue templates.

## [0.3.0] — 2026-10-05

Two skills that build the domain and standards docs with you. Host projects need do nothing; both
skills are opt-in.

### Added
- `/sdlc-pipeline:write-domain`: drafts the five domain files from the project's code and docs,
  marks what it inferred `(to confirm)`, and interviews the user in order (overview, actors,
  glossary, bounded contexts, business rules). Re-runs add to the files and keep `BR-` ids.
- `/sdlc-pipeline:write-standards`: the user picks an architecture template and any concern
  templates, then keeps, adapts or drops every rule. Kept rules are written to `standards/`,
  numbered, with stack blanks filled in. The skill then updates the profile lines that cite
  `standards/`, after showing a diff.
- Standards catalogue in `templates/standards/`: `layered` and `hexagonal` (architecture),
  `testing`, `api` and `persistence` (concerns).
- `scripts/validate.py` checks every catalogue rule has `Why`, `Check` and `Profile` lines and that
  no template names a language, build tool or framework.

### Changed
- `init` suggests `write-domain` and `write-standards` when `domain/` or `standards/` is missing,
  instead of offering a domain skeleton.
- `docs/domain-and-standards.md` and the README describe the two skills.

## [0.2.1] — 2026-10-04

Documentation only. Host projects need do nothing.

### Added
- `docs/domain-and-standards.md`: what goes in `domain/` and `standards/`, how each agent uses them,
  examples, sample prompts for drafting them, and how to tell which docs earn their place.
- A "Domain and standards" section in the README, linked from `docs/pipeline.md` and
  `docs/profile.md`.

## [0.2.0] — 2026-10-04

Records what actually ran. Agent frontmatter says `model: opus`, but that's an alias. Runs have
used other models, and transcripts are eventually deleted. Host projects need do nothing.

### Added
- `session-report` shows the effort each agent ran next to its model, and every Claude Code version
  the session used. Effort is as recorded by Claude Code, or `unknown`.
- `session-report --summary` prints one JSON object with the session id, report path, Claude Code
  version, and the model, effort and runs of the orchestrator and each agent type.
- Retrospectives record `claude_code`, `orchestrator` and `agents` (model, effort and runs) in their
  front matter. `build-use-case` fills them from `--summary`, even when a project's own
  `retrospectives/TEMPLATE.md` predates the fields.

## [0.1.0] — 2026-10-04

First release. Extracted from the `.claude/` folder of
[prule/sdlc](https://github.com/prule/sdlc) at commit `5207798`.

### Added
- `init` skill: checks OpenSpec, drafts `.claude/sdlc-profile.md`, creates the use-cases,
  retrospectives and session-reports folders, and prints the team `settings.json` snippet.
- **Project profile** (`.claude/sdlc-profile.md`, template in `templates/`): the verify and codegen
  commands, paths, git rules, implementation rules, task order and per-gate review checklists.
- `build-use-case` creates the use-case branch before planning, lists the use case's unresolved open
  questions at Gate 1, and checks that the plan covers every flow and business rule.
- `session-report`: `--out-dir` and `--context-dirs` options.
- Docs: `README.md`, `docs/pipeline.md`, `docs/profile.md`, `docs/observability.md`.
- CI: `scripts/validate.py` and `claude plugin validate` on every push.

### Changed
- `build-ticket` is now `build-use-case`, and the pipeline takes use cases only. It can't be
  triggered by the model, only run by the user.
- The agents are stack-agnostic. Java, Gradle, OpenAPI, Flyway and Testcontainers rules moved to the
  project profile.
- Observability hooks ship with the plugin (`hooks/hooks.json`) instead of each project's
  `settings.json`.
- `session-report` matches review gates on the short agent name, so namespaced plugin agents
  (`sdlc-pipeline:qa`) still count as gates. It works out the project's log folder instead of
  hard-coding it.

### Removed
- The `write-ticket` command and the `ticket-writer` agent.
