# SDLC pipeline profile

<!--
This file is read by every sdlc-pipeline agent and skill before it does anything. It holds the facts
about THIS project that the agents need but cannot assume: how to prove the code works, where things
live, the stack rules to follow and what each review gate checks. The agents carry the roles and the
judgment; this file carries the stack. Keep it short: link to standards/ for detail rather than
copying it. Field reference: https://github.com/prule/sdlc-pipeline/blob/main/docs/profile.md

Lines in <angle brackets> are placeholders. Replace them, or delete a line that does not apply.
-->

## Commands

- **Verify:** `<the one command that compiles, tests and lints, e.g. npm test, ./gradlew build>`.
  Every agent runs this to prove its work and pastes the output.
- **Code generation:** `<command, or "none">`. Run it after changing the contract and before
  writing code that depends on it.
- **Never run:** `<commands agents must not run, e.g. a formatter the pre-commit hook owns, a publish
  task>`.

## Paths

- **Domain knowledge:** `domain/` (glossary, business rules, bounded contexts, actors, overview)
- **Standards:** `standards/`
- **Use cases:** `use-cases/`
- **Retrospectives:** `retrospectives/`
- **Session reports:** `reports/sessions/`

## Git

- **Base branch:** `<main | develop>`
- **Branch per use case:** `feat/uc-<n>-<slug>`, cut from the base branch before the pipeline starts
- **Pull requests target:** `<main | develop>`
- **Commits:** `<e.g. Conventional Commits>`

## Implementation rules

<!-- The stack rules the junior dev follows and the reviewers enforce. One line each, linking the
standard that holds the detail. -->

- `<e.g. Contract-first: change the API contract in <path> before any handler code; handlers
  implement the generated interfaces (standards/<file>.md).>`
- `<e.g. Schema changes are new migrations in <path>; never edit an applied migration.>`
- `<e.g. Persistence logic is tested on the production database engine (standards/testing.md).>`

## Task order

<!-- The order the architect writes tasks.md in, so the junior dev can work it top to bottom. -->

1. `<e.g. contract>` → 2. `<generate>` → 3. `<domain>` → 4. `<application>` → 5. `<adapters +
   migration>` → 6. `<inbound handler>` → 7. `<tests at each layer>`

## Review checklist

<!-- What each gate checks, citing the standard for every item. The agents cite these rules in their
findings, so a precise rule here gives a precise finding. -->

### Plan review (spec-reviewer)

- **`standards/<file>.md`:** `<what a plan must show to conform>`

### Verification (qa)

- **`standards/<file>.md`:** `<what must be covered by a test>`

### Code review (senior-dev)

- **`standards/<file>.md`:** `<the smells and violations to reject>`

## Formatting

`<Who formats code and when. e.g. "A pre-commit hook formats code. Agents never format, never run
the formatter and never flag formatting; disabling the formatter is a defect.">`
