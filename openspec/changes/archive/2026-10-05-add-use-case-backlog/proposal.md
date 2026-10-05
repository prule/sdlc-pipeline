## Why

Once a project has its PRD, domain, standards and OpenSpec config, the getting-started guide goes
straight to "write and build use cases" with no view of *which* use cases, or in what order. Teams
pick ideas one at a time, build features nobody can use yet, and reach a working product late. A
planned, ordered backlog of use cases, with the smallest working product (the MVP) first and then
one value-adding use case at a time, gets a usable product out as early as possible and makes every
later run an improvement to something that already works.

## What Changes

- New skill `/sdlc-pipeline:plan-use-cases`. It reads the PRD, the domain docs and any existing use
  cases and OpenSpec specs, proposes the use cases the product needs, interviews the user to agree
  the MVP cut and the order of what follows, and writes `BACKLOG.md` at the project root. On a re-run it
  reads the existing `BACKLOG.md`, keeps every entry's status, catches up statuses for work done
  outside the skills (a use case written by hand, a change archived directly), and proposes
  additions and re-ordering as a diff the user confirms.
- `BACKLOG.md` has a fixed structure, from a new template `templates/backlog.md`:
  - **MVP**: the fewest user-goal use cases that together give the primary actor a working,
    end-to-end product, main flows first. Nothing goes here that the product can launch without.
  - **Increments**: numbered, each one use case (or one extension of an earlier one) that makes the
    product more valuable on its own, ordered by value to the users in the PRD.
  - **Later**: ideas worth keeping that are not yet ordered.
  - Each entry is a checklist item with a title, primary actor, goal, why it sits where it does,
    what it depends on, and a status: not written, written (linked to `use-cases/UC-<n>-<slug>.md`)
    or built (linked to the archived change). Built entries are ticked, and each section heading
    shows its progress, for example `MVP (2/4 built)`.
- `write-use-case`: accepts a `BACKLOG.md` entry as its input (for example "the next one" or an entry
  title), drafts the use case from it, and updates the entry's status and link once the use case is
  saved. With no argument and a `BACKLOG.md` present, it offers the next not-written entry.
- `build-use-case`: after the change is archived, ticks the matching `BACKLOG.md` entry as built and
  names the next entry in its final report. It never edits `BACKLOG.md` on a run that stops before
  archive.
- `init`, `write-domain`, `write-standards`: their next-step hints point to `plan-use-cases` before
  `write-use-case` when no `BACKLOG.md` exists.
- Docs: `docs/getting-started.md` gains a step "Plan the use cases" between the config step and
  writing use cases; README skills table, Quick start and docs list updated; `CHANGELOG.md`.

## Capabilities

### New Capabilities
- `use-case-backlog`: how `plan-use-cases` writes and grows `BACKLOG.md` in a host project (MVP-first
  structure, entry fields and statuses, re-runs), and how `write-use-case` and `build-use-case` keep
  the entries' statuses current.

### Modified Capabilities
None. `run-retrospective` is unchanged: the retrospective is still written on every run, and the
`BACKLOG.md` update is a separate step after archive. `domain-authoring` and `standards-authoring` only
change their next-step hint, which no requirement covers.

## Impact

- **Components:** skills (`plan-use-cases` new; `write-use-case`, `build-use-case`, `init`,
  `write-domain`, `write-standards` changed), templates (`templates/backlog.md` new), docs
  (`README.md`, `docs/getting-started.md`, `docs/pipeline.md`), manifests and `CHANGELOG.md`.
- **Host projects:** need do nothing. `plan-use-cases` is opt-in; `write-use-case` and
  `build-use-case` touch `BACKLOG.md` only when it exists, and only during a run the user started. No
  profile change: `BACKLOG.md` lives at the project root.
- **Semver:** minor bump to 0.6.0 (0.5.0 is the session-report change on this branch's base). It
  adds a user-facing skill and changes what `write-use-case` and `build-use-case` do. No existing
  profile needs editing.
