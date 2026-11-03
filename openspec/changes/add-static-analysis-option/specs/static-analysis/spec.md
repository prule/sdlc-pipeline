# Spec Delta

## Purpose

Lets a host project turn on a static-analysis scan as part of QA, and says how QA and the gates
treat its result.

## ADDED Requirements

### Requirement: The scan is off unless the profile turns it on
The project profile SHALL accept a **Static analysis** setting in its `## Pipeline` section, with
the value `off` or a command. If the setting or the section is missing, the scan SHALL be off. When
the scan is off, QA SHALL NOT run any static-analysis command.

#### Scenario: Profile without the setting
- **WHEN** the profile has no **Static analysis** line
- **THEN** QA runs only the **Verify** command, and its report says `Static analysis: off`

#### Scenario: Setting is off
- **WHEN** the profile says `**Static analysis:** off`
- **THEN** QA runs no scan, and its report says `Static analysis: off`

#### Scenario: New project
- **WHEN** `/sdlc-pipeline:init` creates a profile
- **THEN** its `## Pipeline` section has `**Static analysis:** off`

### Requirement: QA runs the scan after Verify passes
When the setting names a command, QA SHALL run that command once per QA run, after the **Verify**
command passes, and SHALL paste its output in the report. If **Verify** fails, QA SHALL NOT run the
scan, and its report SHALL say `Static analysis: not run (Verify failed)`.

#### Scenario: Scan passes
- **WHEN** the profile says `**Static analysis:** sonar-check`, Verify passes and `sonar-check` exits 0
- **THEN** QA's report contains the scan output and `Static analysis: passed`, and the scan does not change the verdict

#### Scenario: Verify fails
- **WHEN** the scan is on and the Verify command fails
- **THEN** QA does not run the scan and reports `Static analysis: not run (Verify failed)`

### Requirement: Quality-gate failures are defects
When the scan fails its quality gate, QA SHALL report each issue it lists as a defect, SHALL return
NOT READY, and SHALL NOT fix production code. Each issue SHALL appear in the Run-log findings with
kind `code-defect` or `standards-violation` and the analyser's rule key in `rule`. An issue that the
change silences with a suppression comment, with no reason next to it, SHALL also be a defect.

#### Scenario: Scan fails
- **WHEN** the scan exits non-zero and lists 2 issues in files the change touched
- **THEN** QA returns NOT READY with 2 defects and `Static analysis: failed (2 issues)`, and the orchestrator sends them to the implementer as a qa↔implementer fix round

#### Scenario: Re-verify after the fix
- **WHEN** the implementer fixes the issues and QA runs again
- **THEN** QA runs the scan again, and returns READY TO ARCHIVE if it passes and nothing else blocks

### Requirement: A scan that cannot run is an infra issue
When the scan command cannot complete for an environmental reason (the server is unreachable, a
token is missing, the command is not installed), QA SHALL report it once as an infra issue, SHALL
NOT retry it, SHALL report `Static analysis: not run (<reason>)`, and SHALL base its verdict on the
rest of the evidence.

#### Scenario: Server down
- **WHEN** the scan is on and the command reports it cannot reach the analysis server
- **THEN** QA runs it once, reports `Static analysis: not run (server unreachable)` as an infra issue, and returns READY TO ARCHIVE if everything else passes

### Requirement: Gate 2 shows the scan result
At Gate 2, `build-use-case` SHALL show QA's **Static analysis** line with the QA verdict and
evidence.

#### Scenario: Scan not run at Gate 2
- **WHEN** QA reported `Static analysis: not run (server unreachable)`
- **THEN** Gate 2 shows that line, so the human can decide whether to archive without a scan
