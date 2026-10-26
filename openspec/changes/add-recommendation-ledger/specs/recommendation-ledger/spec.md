## ADDED Requirements

### Requirement: The run reads the ledger before planning
When `<retrospectives>/LEDGER.md` exists, `build-use-case` SHALL read its Open lines before it
spawns the architect, and SHALL pass the architect each line that applies to the use case, with
its id. Later agents SHALL receive only the applying lines for their phase. When the file is
missing, the run SHALL continue without it.

#### Scenario: Ledger with an applying line
- **WHEN** the ledger has an Open line `L-8` that targets the testing standard and the use case adds tests
- **THEN** the architect's prompt lists `L-8` with its recommendation under `Ledger lessons`

#### Scenario: No ledger
- **WHEN** the project has no `retrospectives/LEDGER.md`
- **THEN** the run reaches Gate 1 as before, and step 7 creates the ledger

### Requirement: Gate 1 shows due lines
Gate 1 SHALL list each applying Open line with 3 or more records under `Due ledger lines`, or
`none`. For each, the human SHALL be asked to adopt it in this run, keep it open, or close it, and
keeping or closing SHALL need a reason.

#### Scenario: A due line applies
- **WHEN** an applying line has *Records* 4
- **THEN** Gate 1 lists it with its id, target and count, and asks adopt, keep or close

#### Scenario: Nothing due
- **WHEN** no applying line has 3 or more records
- **THEN** Gate 1 shows `Due ledger lines: none`

### Requirement: The retrospective counts recurring recommendations
At step 7 of every run, each recommendation in the record SHALL end with its ledger id. A
recommendation that matches an Open line SHALL add 1 to that line's *Records*, once per record. A
line that reaches 3 records SHALL get *Status* `due`.

#### Scenario: Recurring recommendation
- **WHEN** the record recommends what Open line `L-8` (*Records* 2) says
- **THEN** the record says `· ledger: L-8`, `L-8` has *Records* 3 and *Status* `due`

### Requirement: New open recommendations get a ledger line
A recommendation still open after the run that matches no line SHALL get a new Open line with the
next id and *Records* 1. A recommendation adopted during the run SHALL NOT get a line.

#### Scenario: New recommendation
- **WHEN** the highest id in the ledger is `L-16` and the record has a new open recommendation
- **THEN** the ledger has a new Open line `L-17` with *Records* 1, and the record says `· ledger: L-17 (new)`

### Requirement: Gate 1 answers are written to the ledger
At step 7, adopted and closed lines SHALL move to Closed with the PR, branch or reason, and kept
lines SHALL record the reason in *Status*. No other line SHALL change. The commit reminder SHALL
name `LEDGER.md`.

#### Scenario: Run stopped at Gate 1
- **WHEN** the human stops the run at Gate 1 and closes due line `L-12` with a reason
- **THEN** the retrospective is written, `L-12` is in Closed with `closed: <reason>`, and the commit reminder names `LEDGER.md`

### Requirement: A missing ledger is created and seeded
When `LEDGER.md` is missing at step 7, the run SHALL create it from the plugin's ledger template and
seed it with one line for each unticked recommendation that appears in two or more of the five most
recent records, including this one. `init` SHALL create `LEDGER.md` when it creates the
retrospectives folder.

#### Scenario: Project with records and no ledger
- **WHEN** three of the last five records recommend the same unadopted change and there is no ledger
- **THEN** step 7 creates `LEDGER.md` with that recommendation as `L-1`, *Records* 3, *Status* `due`

#### Scenario: New project
- **WHEN** `init` runs in a project with no retrospectives folder
- **THEN** the folder has `README.md` and a `LEDGER.md` with empty Open and Closed tables
