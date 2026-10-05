# session-report Specification

## Purpose

The session report turns a Claude Code session transcript into an HTML report of the run. It also records which models, effort levels and Claude Code version the run used, so the record outlasts the transcript.

## Requirements

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
Every report run SHALL write the run summary as one JSON object to `<session>.summary.json` beside the HTML report. When run with `--summary`, the session report SHALL also print that same object to stdout, and nothing else. The object SHALL contain: `session` (session id), `report` (path of the written report), `claude_code` (version string, or a list if there are several), `orchestrator` (`model` and `effort` of the main session) and `agents` (keyed by agent type, each with `model`, `effort` and `runs`). It SHALL also contain `schema` (the summary format version), `runs`, `findings`, `fix_loops`, `time` and `tokens`, as set out in the requirements below. Model values SHALL be full model IDs. A `model` or `effort` value that differs across runs SHALL be a comma-separated list. A missing value SHALL be the string `unknown`.

#### Scenario: Summary for a pipeline run
- **WHEN** the script runs on a session with one architect run and two junior-dev runs, using `--summary`
- **THEN** stdout parses as one JSON object whose `agents.architect.runs` is 1 and `agents.junior-dev.runs` is 2, and the HTML report exists at the path in `report`

#### Scenario: Without the option
- **WHEN** the script runs without `--summary`
- **THEN** it prints its usual human-readable status lines and no JSON, and `<session>.summary.json` is written beside the report

#### Scenario: Printed and written summaries match
- **WHEN** the script runs with `--summary`
- **THEN** the object printed to stdout is identical to the contents of `<session>.summary.json`

#### Scenario: Session with no subagents
- **WHEN** the session spawned no agents
- **THEN** `agents` is an empty object, `runs` and `fix_loops` are empty lists, and `orchestrator` is still filled in

### Requirement: Subagent runs are linked exactly
The report SHALL link each subagent transcript to the Agent call that started it using the tool-use id recorded beside the transcript. When no such id is recorded, it SHALL fall back to matching the prompt, and the report SHALL state how many runs were linked by prompt.

#### Scenario: Two runs with the same prompt opening
- **WHEN** two spec-reviewer runs have prompts with the same first 120 characters, and both transcripts record their tool-use ids
- **THEN** each run shows the work from its own transcript

#### Scenario: Older transcript without ids
- **WHEN** a session's subagent transcripts record no tool-use ids
- **THEN** the runs are linked by prompt and the report notes "linked by prompt" with the count

### Requirement: Each run shows its own work
When the orchestrator resumes an agent with a message, the report SHALL credit the tool calls, tokens, files and time that follow the resume to the resumed run, not to the agent's first run.

#### Scenario: Fix run after a QA rejection
- **WHEN** qa rejects a change and the orchestrator resumes junior-dev to fix it, and junior-dev makes 12 tool calls after the resume
- **THEN** the report shows the fix run with 12 tool calls, and the first junior-dev run's count excludes them

#### Scenario: Resume markers missing
- **WHEN** a resumed agent's transcript has no recognisable resume marker, but the main transcript records when each run started
- **THEN** the report still splits the work by the runs' start times, and notes that the markers didn't match

#### Scenario: Resume start time missing
- **WHEN** the main transcript records no start time for a resumed run
- **THEN** the report credits that agent's work to its first run, as before, and notes that per-run work isn't available for that agent

### Requirement: Shell file access is counted
The context and files panels SHALL count reads and writes made through common shell commands as well as through file tools, and SHALL label those counts as including shell access. The files panel SHALL leave out Claude Code's own files (tool results, the scratchpad, transcripts) and SHALL show paths relative to the project root.

#### Scenario: Standard read with cat
- **WHEN** a reviewer runs `cat standards/testing.md` and never uses the Read tool on it
- **THEN** the context panel counts one read of `standards/testing.md` and doesn't list it as never read

#### Scenario: Internal tool-result file
- **WHEN** an agent reads a file under the session's `tool-results/` folder
- **THEN** that file doesn't appear in the files panel

### Requirement: Gate findings are parsed
For each gate run whose hand-back contains a **Run-log findings** block, the report SHALL list every finding in a findings table with its id, gate, run, kind, severity, rule, location and status. A gate run with no such block SHALL fall back to the keyword verdict, marked as inferred. The summary's `findings` list SHALL hold the same entries.

#### Scenario: QA findings block
- **WHEN** a qa hand-back contains `- **Q1** · kind: test-gap · severity: high · rule: standards/testing.md §2 · where: src/a.ts:10 · status: handed-back`
- **THEN** the findings table has a row for Q1 with gate qa, kind test-gap, severity high, rule `standards/testing.md §2` and status handed-back

#### Scenario: Gate run without a block
- **WHEN** a spec-reviewer hand-back says `REQUEST CHANGES` but has no Run-log findings block
- **THEN** the run's verdict shows as REQUEST CHANGES, marked inferred, and no findings rows are added for it

### Requirement: Fix loops are shown
The report SHALL show each fix loop: the gate run whose findings started it, the findings handed back, the run that made the fix, the run that re-checked it, and the time, tool calls and tokens of the fix and re-check. The summary's `fix_loops` list SHALL hold the same.

#### Scenario: One QA loop
- **WHEN** qa hands back Q1 to Q3, junior-dev is resumed to fix them, and qa is resumed to re-verify
- **THEN** the report shows one fix loop started by qa, listing Q1 to Q3, with the fix run and the re-verify run and their combined cost

### Requirement: Time is broken down
The report SHALL split the session's wall time into time agents were working, time waiting on the human, and the remaining orchestrator time. Time waiting on the human SHALL include the time spent in questions to the user and the time between the orchestrator's last message and the user's next prompt while no agent was running. Overlapping agent runs SHALL be counted once. The summary's `time` object SHALL hold the same values in seconds.

#### Scenario: Gate approval wait
- **WHEN** the orchestrator asks for Gate 1 approval and the user answers 3 minutes later, with no agent running in between
- **THEN** those 3 minutes count as waiting on the human, not as agent or orchestrator time

### Requirement: Tokens are shown in full
The report SHALL show input, cache-write, cache-read and output tokens for each run, each agent type and the whole session. It SHALL NOT show prices. The summary's `tokens` object and each entry in `runs` SHALL hold the same counts.

#### Scenario: Agent type totals
- **WHEN** two junior-dev runs used 1,000 and 2,000 output tokens
- **THEN** the junior-dev row shows 3,000 output tokens, alongside its input and cache token totals

### Requirement: Report is laid out for tuning
The report SHALL present, in order: the run's identity and totals; the run as a timeline with fix loops marked; the findings table; the agent table; the context panel. The errors, tool usage, files and activity feed sections SHALL be collapsed by default. When the transcript names a use case file or an OpenSpec change, the header SHALL show them.

#### Scenario: Pipeline run header
- **WHEN** the session ran `build-use-case` on `use-cases/UC-0.1-app-launches.md` and created change `uc-0-1-open-logbook`
- **THEN** the report header shows UC-0.1 and `uc-0-1-open-logbook`

#### Scenario: Diagnostics collapsed
- **WHEN** the report is opened
- **THEN** the errors, tool usage, files and activity feed sections are closed until the reader opens them
