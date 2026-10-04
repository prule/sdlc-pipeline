## Purpose

The session report turns a Claude Code session transcript into an HTML report of the run. It also records which models, effort levels and Claude Code version the run used, so the record outlasts the transcript.

## ADDED Requirements

### Requirement: Report shows the model and effort each agent ran
The session report SHALL show, for each agent type, the full model ID or IDs its runs used and the effort level or levels recorded for them. When the transcript records no effort for an agent, the report SHALL show `unknown`. The report SHALL NOT infer effort from agent frontmatter or defaults.

#### Scenario: Agent ran with a recorded effort
- **WHEN** a subagent transcript's assistant messages record model `claude-opus-5-5` and effort `medium`
- **THEN** that agent's row in the report shows model `opus-5-5` and effort `medium`

#### Scenario: Effort not recorded
- **WHEN** a subagent transcript's assistant messages record a model but no effort
- **THEN** that agent's row shows effort `unknown`

#### Scenario: Agent type ran on more than one model
- **WHEN** two runs of `junior-dev` used `claude-sonnet-5` and `claude-opus-5-5`
- **THEN** the `junior-dev` row lists both models

### Requirement: Report shows the Claude Code version
The session report SHALL show the Claude Code version recorded in the session transcript. When the transcript records more than one version, the report SHALL list each one.

#### Scenario: Single version
- **WHEN** every transcript line records version `2.1.288`
- **THEN** the report header shows `v2.1.288`

### Requirement: Machine-readable run summary
When run with `--summary`, the session report SHALL write the HTML report as usual and print exactly one JSON object to stdout, and nothing else. The object SHALL contain: `session` (session id), `report` (path of the written report), `claude_code` (version string, or a list if there are several), `orchestrator` (`model` and `effort` of the main session) and `agents` (keyed by agent type, each with `model`, `effort` and `runs`). Model values SHALL be full model IDs. A `model` or `effort` value that differs across runs SHALL be a comma-separated list. A missing value SHALL be the string `unknown`.

#### Scenario: Summary for a pipeline run
- **WHEN** the script runs on a session with one architect run and two junior-dev runs, using `--summary`
- **THEN** stdout parses as one JSON object whose `agents.architect.runs` is 1 and `agents.junior-dev.runs` is 2, and the HTML report exists at the path in `report`

#### Scenario: Without the option
- **WHEN** the script runs without `--summary`
- **THEN** it prints its usual human-readable status lines and no JSON

#### Scenario: Session with no subagents
- **WHEN** the session spawned no agents
- **THEN** `agents` is an empty object and `orchestrator` is still filled in
