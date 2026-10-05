# Backlog template

`/sdlc-pipeline:plan-use-cases` writes `BACKLOG.md` at the project root from the block below. Delete
the guidance comments and the example entries.

**The backlog lists use cases, not tasks.** Each entry is one user-goal use case that
`/sdlc-pipeline:write-use-case` will write and `/sdlc-pipeline:build-use-case` will build. Stay at the
business level, in the glossary's terms: no screens, endpoints, tables or technologies.

**Get to a working product first, then improve it one use case at a time.**

1. Name the **primary actor** and the **core goal** from the PRD: the one outcome the product exists
   for.
2. List candidate use cases from the PRD's capabilities. Leave out anything the PRD puts out of
   scope.
3. **MVP:** the shortest path of use cases that lets the primary actor reach the core goal end to
   end, main flows only. Ask of every candidate: *"Can the primary actor reach the core goal without
   this?"* If yes, it is not MVP.
4. **Increments:** one use case each, or one extension of an earlier one (an alternative or exception
   flow, a second actor, a stricter business rule). Order them by value to the PRD's users, and never
   put an entry before one it depends on. Each increment leaves a product someone would rather use
   than the one before.
5. **Later:** everything else worth keeping, not yet ordered.

**Entries.** Each entry is a checklist item. Its first line holds the id, the title and the status;
the skills edit only that line and the section counts. Ids are `B-<n>`, never renumbered or reused.
The box is ticked only when the entry is built.

| Status | First line |
|--------|-----------|
| not written | `- [ ] **B-<n>: <title>**` |
| written | `- [ ] **B-<n>: <title>** — written: [UC-<m>](use-cases/UC-<m>-<slug>.md)` |
| built | `- [x] **B-<n>: <title>** — built: [UC-<m>](use-cases/UC-<m>-<slug>.md), change <change-name>` |

---

```markdown
# Backlog

<!-- Product: <one line from the PRD>. Primary actor: <actor>. Core goal: <the one outcome>.
     Written by /sdlc-pipeline:plan-use-cases; re-run it when the PRD changes. -->

## MVP (1/3 built)

<!-- The fewest use cases that let the primary actor reach the core goal end to end. Main flows only. -->

- [x] **B-1: <title, e.g. "Borrow an item">** — built: [UC-001](use-cases/UC-001-<slug>.md), change <change-name>
  - **Actor:** <primary actor, from domain/actors-and-personas.md>
  - **Goal:** <the outcome, in one business sentence>
  - **Why here:** <why the primary actor can't reach the core goal without it>
  - **Depends on:** None
- [ ] **B-2: <title>** — written: [UC-002](use-cases/UC-002-<slug>.md)
  - **Actor:** <actor>
  - **Goal:** <goal>
  - **Why here:** <reason>
  - **Depends on:** B-1
- [ ] **B-3: <title>**
  - **Actor:** <actor>
  - **Goal:** <goal>
  - **Why here:** <reason>
  - **Depends on:** B-1

## Increments (0/1 built)

<!-- One use case, or one extension of an earlier one, per entry. Most valuable first. -->

- [ ] **B-4: <title>**
  - **Actor:** <actor>
  - **Goal:** <goal>
  - **Why here:** <the value it adds, and why it comes before the next increment>
  - **Depends on:** B-2

## Later (0/1 built)

<!-- Worth keeping, not yet ordered. Move an entry up when it earns a place. -->

- [ ] **B-5: <title>**
  - **Actor:** <actor>
  - **Goal:** <goal>
  - **Why here:** <why it can wait>
  - **Depends on:** None
```
