## ADDED Requirements

### Requirement: Retrospective records the implementer
The retrospective written at the end of every `build-use-case` run SHALL include `implementer` in
its front matter, set to `junior-dev` or `senior-dev`: the agent the run chose for stage 3. A run
that stops before stage 3 SHALL still record the implementer it would have used. The field SHALL
be added even when the project's retrospective template lacks it, and the template SHALL NOT be
modified.

#### Scenario: Senior implementer run
- **WHEN** a run with `--senior` ends with the change archived
- **THEN** its retrospective's front matter has `implementer: senior-dev`, and the `agents` block shows `senior-dev` with `runs` counting both the implement run and the code-review run

#### Scenario: Run stopped at Gate 1
- **WHEN** the profile says `**Implementer:** senior-dev` and the human stops the run at Gate 1
- **THEN** the retrospective has `implementer: senior-dev`

#### Scenario: Older project template
- **WHEN** `retrospectives/TEMPLATE.md` has no `implementer` field and a run ends
- **THEN** the new retrospective has `implementer`, and `TEMPLATE.md` is unchanged
