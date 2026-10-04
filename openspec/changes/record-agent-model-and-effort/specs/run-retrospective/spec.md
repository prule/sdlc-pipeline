## Purpose

Every build-use-case run leaves a retrospective in the host project: a committed record of what the gates caught and what to change. This capability covers the run facts its front matter records, including the models and effort the run's agents used.

## ADDED Requirements

### Requirement: Retrospective records the models and effort used
The retrospective written at the end of every `build-use-case` run SHALL include in its front matter `claude_code`, `orchestrator` (model and effort) and `agents` (model, effort and runs per agent type). The values SHALL come from the session report's summary for that run's session, not from agent frontmatter.

#### Scenario: Archived run
- **WHEN** a run ends with the change archived
- **THEN** its retrospective's front matter has `claude_code`, `orchestrator` and an `agents` entry for every agent type that ran, each with `model`, `effort` and `runs`

#### Scenario: Run stopped at a gate
- **WHEN** a run stops at Gate 1 after the architect and spec-reviewer ran
- **THEN** the retrospective's `agents` block lists `architect` and `spec-reviewer` only

#### Scenario: Agent ran on a model other than its frontmatter alias
- **WHEN** `junior-dev`'s frontmatter says `model: opus` but its runs used `claude-sonnet-5`
- **THEN** the retrospective records `junior-dev` with model `claude-sonnet-5`

### Requirement: Fields are added even with an older project template
When the host project has its own retrospective template that lacks the `claude_code`, `orchestrator` or `agents` fields, the retrospective SHALL still include them. The project's template file SHALL NOT be modified.

#### Scenario: Project template predates the fields
- **WHEN** `retrospectives/TEMPLATE.md` has no `agents` field and a run ends
- **THEN** the new retrospective has the `agents` block, and `TEMPLATE.md` is unchanged

### Requirement: Unknown values are recorded as unknown
When the session summary can't be produced, or reports `unknown` for a value, the retrospective SHALL record `unknown` for that value and SHALL NOT fill it from frontmatter or defaults.

#### Scenario: Session report fails
- **WHEN** the session report script fails at the end of a run
- **THEN** the retrospective is still written, with `claude_code: unknown`, `orchestrator` and `agents` set to `unknown`, and the Summary notes that the session report failed
