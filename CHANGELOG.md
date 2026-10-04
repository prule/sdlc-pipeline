# Changelog

All notable changes to this plugin. Versions follow [semver](https://semver.org/); before 1.0, a
change that requires projects to edit their profile bumps the minor version.

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
