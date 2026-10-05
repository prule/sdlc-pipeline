# use-case-backlog Specification

## Purpose
The `plan-use-cases` skill turns a host project's PRD and domain docs into `BACKLOG.md`: an ordered
backlog of use cases that reaches a working MVP first and then adds value one use case at a time.
`write-use-case` and `build-use-case` keep each entry's status current as the backlog is worked.

## Requirements

### Requirement: Writes an MVP-first backlog to BACKLOG.md
When run, `plan-use-cases` SHALL write `BACKLOG.md` at the project root with three sections in this
order: **MVP**, **Increments** and **Later**. The MVP section SHALL hold the fewest user-goal use
cases that together let the primary actor reach the product's core goal from the PRD end to end.
Each Increment SHALL be one use case, or one extension of an earlier use case, that adds value on its
own. Increments SHALL be ordered by value to the PRD's users, and no entry SHALL come before an entry
it depends on. Ideas not yet ordered SHALL go under Later.

#### Scenario: Lending library PRD
- **WHEN** the PRD's core goal is "members borrow and return items", and it also mentions holds,
  overdue reminders and usage reports
- **THEN** the MVP section contains the use cases a member needs to borrow and return an item, and
  holds, overdue reminders and usage reports are Increments or Later entries, not MVP entries

#### Scenario: Dependency order
- **WHEN** the Increment "Place a hold on an item" depends on the MVP entry "Borrow an item"
- **THEN** "Borrow an item" appears before "Place a hold on an item" in `BACKLOG.md`

### Requirement: The MVP stays minimal
The skill SHALL keep an entry out of the MVP unless the user confirms the product can't be used
without it. When the user asks to add an entry to the MVP, the skill SHALL ask whether the primary
actor can reach the core goal without it, and SHALL place it in Increments if they can. MVP entries
SHALL cover main flows only; an alternative or exception flow that the product can launch without
SHALL be its own Increment.

#### Scenario: User asks for a non-essential MVP entry
- **WHEN** the user asks to add "Export usage reports" to the MVP and confirms members can borrow and
  return without it
- **THEN** "Export usage reports" is written as an Increment, not an MVP entry

#### Scenario: Deferring an exception flow
- **WHEN** the MVP entry "Borrow an item" could also handle "item is reserved for another member"
- **THEN** that course is a separate Increment, unless the user confirms the MVP can't launch without
  it

### Requirement: Entries have stable ids, fixed fields and a status
Every entry SHALL have an id of the form `B-<n>`, a title, a primary actor, a goal, the reason it sits
where it does, the ids it depends on, and a status. The status SHALL be one of `not written`,
`written` (with a link to the use-case file) or `built` (with the use-case link and the archived
change's name). Ids SHALL NOT change when entries are re-ordered or moved between sections, and a
deleted entry's id SHALL NOT be reused.

#### Scenario: Re-ordering keeps ids
- **WHEN** the user moves B-7 from Later to the first Increment on a re-run
- **THEN** the entry is still B-7, and no other entry's id changes

### Requirement: Built entries are ticked off
Every entry SHALL be a Markdown task-list item whose box is ticked (`- [x]`) when, and only when, its
status is `built`. Each section heading SHALL show how many of its entries are built out of how many
it holds (for example `MVP (2/4 built)`), and every skill that changes a status SHALL update the
count.

#### Scenario: Last MVP entry built
- **WHEN** the MVP section has four entries, three built, and the fourth's change is archived
- **THEN** the fourth entry's box is ticked and the heading reads `MVP (4/4 built)`

#### Scenario: Written but not built
- **WHEN** B-4's use case is written but not yet built
- **THEN** B-4's box is not ticked and its first line links to the use case

### Requirement: The backlog is grounded in the PRD and the domain
The skill SHALL read the PRD (usually `docs/prd.md`), the domain docs and `openspec/config.yaml`
before proposing entries. Entries SHALL use glossary terms and actors from the domain docs and SHALL
stay at the business level: no screens, endpoints, tables or technologies. Anything the PRD marks out
of scope SHALL NOT appear as an entry. If no PRD exists, the skill SHALL tell the user the backlog
depends on one, suggest writing it with `grill-me`, and SHALL NOT write `BACKLOG.md` unless the user
chooses to continue from an interview alone.

#### Scenario: Out-of-scope capability
- **WHEN** the PRD lists "payments" as out of scope
- **THEN** `BACKLOG.md` has no entry about payments

#### Scenario: No PRD
- **WHEN** the user runs `plan-use-cases` in a project with no PRD and declines to continue
- **THEN** no `BACKLOG.md` is written and the skill suggests `grill-me`

### Requirement: Existing work is reflected in the backlog
On a first run in a project that already has use cases or archived changes, the skill SHALL add an
entry for each existing use case with status `written`, or `built` when a matching archived change
exists, and SHALL NOT propose a duplicate of any of them.

#### Scenario: Brownfield project
- **WHEN** `use-cases/UC-001-borrow-an-item.md` exists and its change is archived
- **THEN** `BACKLOG.md` has an entry "Borrow an item" with status `built`, linked to UC-001 and the
  archived change, and no other entry duplicates it

### Requirement: Re-runs keep the backlog's history and catch up its statuses
When `BACKLOG.md` exists, the skill SHALL read it, propose additions, moves and re-ordering as a diff,
and write only after the user confirms. It SHALL NOT delete an entry or move a `written` or `built`
entry out of its section unless the user asks it to. It SHALL NOT move a status backwards. It SHALL
propose moving a status forwards where the project shows the work was done outside the skills: an
entry with no link whose use case now exists becomes `written`, and a `written` entry whose change is
archived becomes `built` and is ticked.

#### Scenario: Change archived by hand
- **WHEN** B-3 is `written` with a link to UC-004, and UC-004's change was archived with
  `/opsx:archive` instead of `build-use-case`
- **THEN** the re-run's diff ticks B-3 and marks it `built` with the change name

#### Scenario: Re-run after two builds
- **WHEN** B-1 and B-2 are `built`, and the user runs `plan-use-cases` after adding a capability to
  the PRD
- **THEN** B-1 and B-2 keep status `built`, and the new capability appears as a proposed entry in the
  diff shown before writing

### Requirement: write-use-case drafts from a backlog entry and records it
When `BACKLOG.md` exists, `write-use-case` SHALL accept a backlog entry id, an entry title, or "next" as
its input, and SHALL draft the use case from that entry's actor and goal. With no input, it SHALL
offer the first unticked entry with no use case, in `BACKLOG.md` order. After saving the use case, it SHALL set the
entry's status to `written` with a link to the file. A use case written from an idea that has no
entry SHALL be added to `BACKLOG.md` only if the user agrees, in the section the user picks.

#### Scenario: Writing the next entry
- **WHEN** B-1 is `built`, B-2 is `not written`, and the user runs `write-use-case next`
- **THEN** the use case is drafted for B-2, and after it is saved B-2's status is `written` with a
  link to the new `use-cases/UC-<n>-<slug>.md`

#### Scenario: No BACKLOG.md
- **WHEN** no `BACKLOG.md` exists and the user runs `write-use-case` with an idea
- **THEN** the use case is drafted and saved as before, and no `BACKLOG.md` is created

### Requirement: build-use-case marks an entry built only after archive
When `BACKLOG.md` has an entry linked to the use case being built, `build-use-case` SHALL set that
entry's status to `built` with the archived change's name and tick its box after the change is
archived, and SHALL
name the next `not written` or `written` entry in its final report. It SHALL NOT edit `BACKLOG.md` on a
run that stops, escalates or aborts before archive.

#### Scenario: Archived run
- **WHEN** a run for UC-002, linked from B-2, ends with the change archived
- **THEN** B-2's status is `built` with the change name, and the final report names the next entry

#### Scenario: Run stopped at Gate 1
- **WHEN** a run for UC-002 stops at Gate 1
- **THEN** `BACKLOG.md` is unchanged
