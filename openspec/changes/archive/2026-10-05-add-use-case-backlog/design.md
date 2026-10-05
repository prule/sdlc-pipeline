## Context

Setup today runs PRD → `init` → `write-domain` → `write-standards` → config and README → use cases
(`docs/getting-started.md`). `write-use-case` takes a rough idea and saves
`use-cases/UC-<n>-<slug>.md`. `build-use-case` runs the pipeline for one use case and ends with an
archive (step 6) and a retrospective (step 7). Nothing links one use case to the next or says which
comes first. See proposal.md for motivation and specs/use-case-backlog/spec.md for the requirements.

## Goals / Non-Goals

**Goals:**
- One file a person reads to see what the product will be, what the MVP is, and what is next.
- The MVP cut is argued for, not assumed: every MVP entry has a reason, and the skill pushes back on
  scope creep.
- `BACKLOG.md` stays current without extra effort, because the skills that write and build use cases
  update it.

**Non-Goals:**
- Writing the use cases themselves. `plan-use-cases` lists entries; `write-use-case` writes them.
- Estimates, dates, owners or sprints. The backlog orders by value and dependency only.
- Running several use cases in one pipeline run, or building the backlog automatically.
- A profile field for the backlog path.

## Decisions

### D1. A new skill, not a mode of `write-use-case`

`plan-use-cases` is its own interactive skill, like `write-domain` and `write-standards`.

*Why:* planning the whole product and writing one use case are different conversations. One looks at
the PRD as a whole and cuts scope; the other goes deep on one behaviour. Keeping them apart keeps each
prompt short and lets `write-use-case` stay as it is when there is no `BACKLOG.md`.

*Alternative:* a `--plan` argument to `write-use-case`. Rejected: one skill with two jobs is harder to
trigger correctly and harder to evaluate.

### D2. `BACKLOG.md` at the project root, fixed name, no profile field

*Why:* the file is an ordered backlog of use cases, not a task list, and "backlog" is the word teams
already use for that. Upper case matches the other root files people look for first (`README.md`,
`CHANGELOG.md`). A profile field would make this a profile change for no gain.

*Alternative:* `TODO.md`, the name first asked for. Rejected: it suggests loose tasks and is often
already taken by a developer's own notes.

*Alternative:* `use-cases/BACKLOG.md` or a `Backlog:` profile path. Rejected for now; it can be added
later without breaking anyone, since the default would stay the root file.

### D3. How the skill makes the MVP cut

The skill is told to work in this order, and the template's header comment repeats it:

1. From the PRD, name the **primary actor** and the **core goal** (the one outcome the product exists
   for).
2. List candidate use cases from the PRD's capabilities, at user-goal level, in glossary terms. Drop
   anything the PRD puts out of scope.
3. **MVP** = the shortest path of use cases that lets the primary actor reach the core goal end to
   end, main flows only. Test each candidate with one question: *"Can the primary actor reach the
   core goal without this?"* If yes, it is not MVP.
4. **Increments**: one use case each, or one extension of an earlier one (an alternative or
   exception flow, a second actor, a business rule tightened). Order by value to the PRD's users,
   then by dependency. Each increment should leave a product someone would rather use than the one
   before.
5. **Later**: everything else worth keeping.

The interview (`AskUserQuestion`) confirms the primary actor and core goal first, then shows the MVP
cut with each entry's reason, then the increment order. People correct a draft faster than they
write one, as in `write-domain`.

*Why a single test question:* "MVP ASAP" fails by scope creep one reasonable-sounding addition at a
time. A fixed question, asked for every candidate and every user request to add to the MVP, makes the
cut checkable and gives the user the reason in their own terms.

*Alternative:* MoSCoW or value/effort scoring. Rejected: effort is the architect's call and isn't
known yet, and categories without an ordering don't say what to build next.

### D4. Entry format: a tickbox per entry, ticked when built

```markdown
- [ ] **B-3: Return an item** — written: [UC-004](use-cases/UC-004-return-an-item.md)
  - **Actor:** Member
  - **Goal:** Give a borrowed item back so it can be lent again.
  - **Why here:** Without returns no item is ever available twice; the MVP loop isn't closed.
  - **Depends on:** B-2
```

Each entry is one task-list item. The first line carries everything the skills update; the indented
lines are the entry's detail.

| Status | First line |
|--------|-----------|
| not written | `- [ ] **B-3: Return an item**` |
| written | `- [ ] **B-3: Return an item** — written: [UC-004](…)` |
| built | `- [x] **B-3: Return an item** — built: [UC-004](…), change add-return-an-item` |

The tick means *built*: the change is archived and the product does it. Rendered on GitHub or in an
editor, the backlog reads as a checklist, and the MVP section shows at a glance how close the MVP is.
Each section heading ends with a count the skills keep current, for example `## MVP (2/4 built)`.

Ids are `B-<n>`, assigned in the order entries are first written, never renumbered or reused (the
same rule as `BR-` ids). They are separate from `UC-<n>`, because a UC number is assigned only when a
use case is written, and some entries never are.

*Alternative:* headings per entry with a `Status:` line. Rejected: nothing is ticked off, so progress
isn't visible without reading every entry. *Alternative:* moving built entries to a "Done" section.
Rejected: it breaks the MVP/Increments structure that explains why each entry was built when it was.

### D5. `write-use-case` and `build-use-case` changes are small and conditional

`write-use-case` step 1 adds: if `BACKLOG.md` exists, read it; resolve `B-<n>`, a title or "next" to an
entry and use its actor and goal as the idea; with no argument, offer the first unticked entry with no use case.
Step 4 adds: append `— written: <link>` to that entry's first line. A new idea with no entry is
offered to `BACKLOG.md`, never added silently.

`build-use-case` gets a new step between archive (6) and record the run (7): if `BACKLOG.md` has an
entry linked to this use case, tick its box, change `written` to `built` with the change name, and update the section count, and name the next
entry (the first `written`, else the first `not written`). Placing it after step 6 means a run that
stops before archive never reaches it, which is what the spec requires. Step 7 stays the last step
and still runs on every exit.

Current wording in `build-use-case` step 6: *"On approval, invoke the `openspec-archive-change` skill
for the change to fold the spec deltas into the main specs. Report the final status."* It stays; the
new step follows it.

### D6. Stack-agnostic and leaves OpenSpec alone

The skill, template and doc changes are about business use cases only, so they name no stack. The
template sits under `templates/`, outside `templates/standards/`, so validate.py's catalogue checks
don't apply; it names no technology anyway. Nothing touches OpenSpec's workflow: `BACKLOG.md` is read by
the plugin's skills only, and the archived change name is read from what the archive step reports.

## Risks / Trade-offs

- [The skill accepts every PRD capability into the MVP] → the D3 test question is asked per entry and
  each MVP entry must carry a "Why here" that answers it; the spec scenario with a lending library is
  the manual check.
- [People edit `BACKLOG.md` by hand and break the format] → the skills look entries up by `B-<n>` and
  edit only an entry's first line and the section counts; if an entry can't be found, they say so and leave the file alone
  rather than rewrite it.
- [A use case written without the backlog drifts from it] → `write-use-case` offers to add it; a
  re-run of `plan-use-cases` picks up any use case with no entry (spec: existing work is reflected).
- [The backlog goes stale as the product changes] → `plan-use-cases` is re-runnable and keeps
  history; `docs/getting-started.md` says to re-run it when the PRD changes, like step 5.

## Migration Plan

None needed. Projects without `BACKLOG.md` see no change in `write-use-case` or `build-use-case`.
Rollback is reverting the release; a `BACKLOG.md` already written stays as a plain Markdown file.
