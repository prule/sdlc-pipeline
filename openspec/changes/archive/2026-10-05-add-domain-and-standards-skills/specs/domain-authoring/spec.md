## Purpose

The `write-domain` skill builds and grows a host project's `domain/` docs (overview, actors and personas, glossary, bounded contexts and business rules). It drafts what it can from the project's own sources and interviews the user for the rest.

## ADDED Requirements

### Requirement: Drafts the five domain files from project sources
When run, `write-domain` SHALL read the project's code, README, `CLAUDE.md`, docs and existing use cases, and draft the five domain files in the profile's domain folder (default `domain/`): `overview.md`, `actors-and-personas.md`, `glossary.md`, `bounded-contexts.md` and `business-rules.md`. Every entry the skill inferred rather than found stated in a source SHALL be marked `(to confirm)` until the user confirms it.

#### Scenario: Brownfield project with no domain folder
- **WHEN** the user runs `write-domain` in a project whose code and README use the terms "member" and "loan", and no `domain/` folder exists
- **THEN** the draft `glossary.md` contains entries for Member and Loan, and each entry not confirmed by the user is marked `(to confirm)`

#### Scenario: Greenfield project
- **WHEN** the user runs `write-domain` in a project with no code and no docs
- **THEN** the skill drafts nothing from sources and builds every file from the interview

### Requirement: Interviews in dependency order
The skill SHALL interview the user to confirm inferred entries and fill gaps, in this order: overview, actors and personas, glossary, bounded contexts, business rules. It SHALL NOT ask about anything the sources already state unambiguously.

#### Scenario: Order of questions
- **WHEN** the skill interviews the user on a project with no domain docs
- **THEN** its questions about the overview come before questions about actors, and questions about business rules come last

#### Scenario: Term already defined in sources
- **WHEN** the README defines "Hold" as a member's place in the queue for an item on loan
- **THEN** the skill does not ask the user to define Hold

### Requirement: Business rules have stable ids
Every rule in `business-rules.md` SHALL have an id of the form `BR-<AREA>-<n>`. On a re-run, existing ids SHALL NOT change, and a new rule SHALL take the next free number in its area.

#### Scenario: Adding a rule on a re-run
- **WHEN** `business-rules.md` contains BR-LOAN-1 and BR-LOAN-2, and the user adds a new loan rule on a re-run
- **THEN** the new rule is BR-LOAN-3 and BR-LOAN-1 and BR-LOAN-2 are unchanged

### Requirement: Re-runs add to the docs without losing content
When domain files already exist, the skill SHALL read them, propose additions and changes, and write only after the user confirms. It SHALL NOT delete or rewrite an existing entry unless the user asks it to.

#### Scenario: Existing glossary
- **WHEN** `glossary.md` already defines Member, and the user runs `write-domain` again
- **THEN** the Member entry is unchanged after the run unless the user asked to change it

### Requirement: Domain docs stay at the business level
The files the skill writes SHALL NOT describe implementation: no tables, endpoints, classes, screens or technologies.

#### Scenario: Source describes a database table
- **WHEN** the code has a `loans` table with a `due_date` column
- **THEN** the domain docs describe a Loan and its due date in business terms and do not mention the table or column

### Requirement: Init points to write-domain
When the profile's domain folder is missing, `init` SHALL tell the user the agents rely on it and suggest `/sdlc-pipeline:write-domain`. `init` SHALL NOT create the domain folder itself.

#### Scenario: Init on a project without domain docs
- **WHEN** the user runs `init` in a project with no `domain/` folder
- **THEN** `init`'s report suggests `/sdlc-pipeline:write-domain` and no `domain/` folder exists afterwards
