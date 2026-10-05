---
name: plan-use-cases
description: Plan the product's use cases as an MVP-first backlog in BACKLOG.md, from the PRD and domain docs, by interviewing the user to agree the MVP cut and the order of the increments after it. Re-runs add to the backlog and catch up statuses. Use when the user wants to plan, list, order or prioritise use cases, define the MVP, write a backlog, roadmap or BACKLOG.md, or decide what to build next.
argument-hint: "[focus, e.g. \"re-order the increments\"]"
---

Plan the product as an ordered **backlog of use cases** in `BACKLOG.md` at the project root. The aim
is a **working product (the MVP) as soon as possible**, then one use case at a time that makes it
more valuable. Focus from the user, if any:

$ARGUMENTS

The file's structure, the MVP-cut method and the entry format are set by
`${CLAUDE_PLUGIN_ROOT}/templates/backlog.md`. Read it first and follow it.

## Steps

1. **Load context.** Read `.claude/sdlc-profile.md` for the domain and use-case paths (defaults
   `domain/` and `use-cases/`; if the profile is missing, use the defaults and suggest
   `/sdlc-pipeline:init`). Then read:
   - the PRD (usually `docs/prd.md`);
   - the domain docs, for the actors and the glossary terms;
   - `openspec/config.yaml`;
   - the existing use cases, `openspec/specs/` and `openspec/changes/archive/`, to know what is
     already written and built;
   - `BACKLOG.md`, if it exists. If it does, this is a re-run: go to step 6 after step 2.

2. **Check for a PRD.** If there is none, tell the user the backlog's MVP cut depends on the PRD's
   goals, users and scope, and suggest writing one first with `/mattpocock-skills:grill-me`. Ask
   whether to stop or to continue from an interview alone. If they stop, write nothing.

3. **Draft the backlog** with the template's method:
   - Name the primary actor and the core goal.
   - List candidate use cases at user-goal level, in glossary terms. Leave out anything the PRD puts
     out of scope.
   - Add an entry for every existing use case: `written` with its link, or `built` and ticked when
     its change is archived (match the change to the use case by the use case's id or title in the
     archived proposal). Don't propose a candidate that duplicates one.
   - Cut the MVP with the test question, then order the Increments by value and dependency, and put
     the rest under Later. Give every entry a **Why here** that answers why it sits where it does.

4. **Interview, in this order.** Use `AskUserQuestion` and show your draft as the options; people
   correct a draft faster than they write one. Keep each round small.
   1. The primary actor and the core goal.
   2. The MVP cut: each MVP entry with its Why here, and the entries you kept out of it.
   3. The order of the Increments.

   Don't ask what the PRD already states clearly.

5. **Write** `BACKLOG.md` from the template's block: ids `B-1`, `B-2`… in the order entries are first
   written, statuses as in the template, the built count on every section heading. Show it to the
   user before writing.

6. **Re-run.** When `BACKLOG.md` exists, read it and propose changes as a diff. Write only after the
   user confirms.
   - **Catch up statuses.** An entry with no link whose use case now exists becomes `written`. A
     `written` entry whose change is archived becomes `built` and is ticked. This catches work done
     outside the skills, such as a use case written by hand or a change archived with
     `/opsx:archive`.
   - **Add** entries for new PRD capabilities and for use cases that have no entry.
   - **Move or re-order** entries the user asks about, or that the PRD's changes call for.
   - Recount every section heading.

7. **Report** how many entries are in each section and how many are built, the MVP's reason in one
   line, and any entries whose status you caught up. Suggest the next step:
   `/sdlc-pipeline:write-use-case next` to write the first entry with no use case.

## Rules

- **Guard the MVP.** Whenever the user asks to add an entry to the MVP, ask: *"Can the primary actor
  reach the core goal without this?"* If they can, put it in Increments and say why. An alternative
  or exception flow the product can launch without is its own Increment, not part of an MVP entry.
- **Stable ids.** `B-<n>` ids never change when entries move, and a deleted entry's id is never
  reused. A new entry takes the next number after the highest ever used.
- **Keep history.** Never delete an entry, move a `written` or `built` entry out of its section, or
  move a status backwards, unless the user asks to.
- **Ticks mean built.** Tick an entry's box only when its status is `built`, and keep every
  section's built count right.
- **Edit by entry.** When the file has been edited by hand, find entries by their `B-<n>` id. If an
  entry or the format can't be found, say so and propose the fix rather than rewriting the file.
- **Business level only.** Titles and goals use glossary terms and actors from the domain docs. No
  screens, endpoints, tables or technologies.
- **Don't invent scope.** A capability the PRD doesn't mention is a question for the user, not an
  entry.
