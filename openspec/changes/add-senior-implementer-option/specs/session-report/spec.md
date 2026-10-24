## ADDED Requirements

### Requirement: A senior-dev implement run is not a gate run
The report SHALL treat a `senior-dev` run whose Agent description starts with `Implement` as a
builder run, not a gate run. Such a run SHALL get no verdict and no findings rows. It SHALL count
as a fix run in a fix loop, the same as a `junior-dev` run. Compare mode's `gate_runs` metric SHALL
not count it. Every other `senior-dev` run SHALL stay a gate run.

#### Scenario: Senior implements, QA loops once
- **WHEN** a session has a `senior-dev` run described "Implement UC-4", then qa returns NOT READY with Q1, then that senior-dev run is resumed to fix Q1, then qa re-verifies
- **THEN** the report shows one fix loop started by qa, with the senior-dev resume as its fix run and the second qa run as its re-check, and the implement run has no verdict

#### Scenario: Senior code review after a senior implementation
- **WHEN** the same session later has a `senior-dev` run described "Code review UC-4" that says APPROVE
- **THEN** that run is a gate run with its verdict, and compare mode's `gate_runs` counts it but not the implement run

### Requirement: Per-agent catch rate counts gate runs only
When one agent type has both gate runs and builder runs in a session, the per-agent table SHALL
compute its catch rate over its gate runs only, and SHALL mark it as a gate.

#### Scenario: Senior dev with one implement run and one review run
- **WHEN** `senior-dev` has an implement run and a code-review run that fixed two issues in place
- **THEN** the per-agent table shows `senior-dev` as a gate with "caught 1/1", not "caught 1/2"
