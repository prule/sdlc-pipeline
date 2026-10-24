# implementer-choice Specification

## Purpose

Lets a host project, or a single `build-use-case` run, choose whether `junior-dev` or `senior-dev`
implements the approved plan. Under either choice the pipeline keeps an independent code review.

## Requirements

### Requirement: Profile sets the default implementer
The project profile SHALL accept an **Implementer** setting with the value `junior-dev` or
`senior-dev`, in a `## Pipeline` section. `build-use-case` SHALL use that value as the implementer
for the run unless a run flag overrides it. If the section or setting is missing, the implementer
SHALL be `junior-dev`.

#### Scenario: Profile chooses the senior dev
- **WHEN** the profile's `## Pipeline` section says `**Implementer:** senior-dev` and the run has no flag
- **THEN** stage 3 spawns `sdlc-pipeline:senior-dev` to implement, and `junior-dev` is not spawned

#### Scenario: Profile without the setting
- **WHEN** the profile has no `## Pipeline` section
- **THEN** stage 3 spawns `sdlc-pipeline:junior-dev`, as before this change

### Requirement: A run flag overrides the profile
`build-use-case` SHALL accept `--senior` or `--junior` before the use case. `--senior` SHALL make
`senior-dev` the implementer for that run, and `--junior` SHALL make it `junior-dev`, whatever the
profile says. The flag SHALL NOT change the profile. If both flags are given, the orchestrator SHALL
ask the human which one to use before stage 1.

#### Scenario: Senior for one run
- **WHEN** the profile says `**Implementer:** junior-dev` and the user runs `/sdlc-pipeline:build-use-case --senior use-cases/UC-4-renew-loan.md`
- **THEN** stage 3 spawns `senior-dev`, the profile file is unchanged, and the next run without a flag uses `junior-dev`

#### Scenario: Junior for one run
- **WHEN** the profile says `**Implementer:** senior-dev` and the user passes `--junior`
- **THEN** stage 3 spawns `junior-dev`

#### Scenario: Both flags
- **WHEN** the user passes both `--senior` and `--junior`
- **THEN** the orchestrator asks which implementer to use and spawns no agent until the human answers

### Requirement: Gate 1 shows the implementer
At Gate 1 the orchestrator SHALL state which agent will implement and where that choice came from:
`profile`, `flag` or `default`. If the human names the other implementer in their Gate 1 answer,
the run SHALL use the agent they name.

#### Scenario: Implementer from the flag
- **WHEN** the run was started with `--senior`
- **THEN** Gate 1 shows `Implementer: senior-dev (flag)`

#### Scenario: Human switches at Gate 1
- **WHEN** Gate 1 shows `Implementer: senior-dev (profile)` and the human answers "proceed with the junior dev"
- **THEN** stage 3 spawns `junior-dev`

### Requirement: The senior dev implements to the same plan rules
When spawned to implement, `senior-dev` SHALL work the change's `tasks.md` through `opsx:apply`,
follow the profile's Implementation rules, and paste the Verify command's output. It SHALL stop and
report a blocker or plan defect instead of changing the design. It SHALL return the same report as
the junior dev: tasks done, files changed, Verify output and blockers.

#### Scenario: Plan defect found while implementing
- **WHEN** the senior dev, implementing, finds that a task contradicts the spec delta
- **THEN** it stops and reports the defect, and the orchestrator routes it to the architect

#### Scenario: Implementation report
- **WHEN** the senior dev finishes implementing
- **THEN** its report lists the completed tasks, the files changed and the pasted Verify output

### Requirement: QA defects go back to the implementer
When QA returns NOT READY, the orchestrator SHALL send the defects to the agent that implemented the
change. The qa↔implementer loop SHALL keep its cap of 2 rounds.

#### Scenario: Senior implementer fixes QA defects
- **WHEN** `senior-dev` implemented the change and QA returns NOT READY with Q1 and Q2
- **THEN** the orchestrator sends Q1 and Q2 to that same senior-dev run, not to `junior-dev`, then re-runs QA

### Requirement: Code review stays independent
Stage 5 SHALL always run. When `senior-dev` implemented the change, the orchestrator SHALL spawn a
new `senior-dev` run for the code review. It SHALL NOT resume the implementing run, and it SHALL
pass the reviewer only the change name, not the implementer's report. The review SHALL work as it
does when the junior dev implements: it fixes findings in place and hands back design calls.

#### Scenario: Review after a senior implementation
- **WHEN** `senior-dev` implemented the change and QA returned READY TO ARCHIVE
- **THEN** the orchestrator spawns a new `sdlc-pipeline:senior-dev` run for the code review, and Gate 2 shows its findings as for any run

### Requirement: Default runs are unchanged
When the implementer is `junior-dev`, every stage, gate, fix loop and budget guardrail SHALL behave
as it did before this change.

#### Scenario: Default run
- **WHEN** a project with no `## Pipeline` section runs `build-use-case` with no flag
- **THEN** the agents spawned, in order, are architect, spec-reviewer, junior-dev, qa and senior-dev, as before
