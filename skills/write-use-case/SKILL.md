---
name: write-use-case
description: Interactively draft a business use case (behaviour, not intent; no implementation), grounded in the project's domain docs, and save it to the use-cases directory. Use when the user wants to write, draft or author a use case before running the delivery pipeline.
argument-hint: "<rough idea, a backlog entry id (B-3) or title, or \"next\">"
---

Help the user author a **business use case**. A use case describes **behaviour** end-to-end and stays
at the **business level**: NO implementation (no protocols, endpoints, status codes, data formats,
screens, databases, frameworks or classes — all of that is the architect's job downstream). Idea from
the user:

$ARGUMENTS

## Steps

1. **Load context.** Read `.claude/sdlc-profile.md` for the domain and use-case paths (defaults
   `domain/` and `use-cases/`; if the profile is missing, suggest `/sdlc-pipeline:init` and use the
   defaults). Read the domain docs (overview, glossary, bounded contexts, actors and personas,
   business rules) and the template — the project's `<use-cases>/TEMPLATE.md` if it exists, otherwise
   `${CLAUDE_PLUGIN_ROOT}/templates/use-case.md`. Skim existing use cases and `openspec/specs/` so the
   use case uses the right actors, language and context and doesn't duplicate prior work. Do NOT cite
   implementation standards in the use case — it's business-level.

   **Backlog.** If `BACKLOG.md` exists at the project root, read it and resolve the input to an entry:
   a `B-<n>` id, an entry title, or `next` (the first unticked entry with no use case linked). With no
   input, offer that first entry. Use the entry's actor and goal as the idea. If the input names an
   entry that can't be found, say so and ask for the idea instead. Without a `BACKLOG.md`, the input
   is the idea, as before.

2. **Interview the user for the gaps.** Ask only what you genuinely can't infer — use `AskUserQuestion`
   for the decisions that shape the behaviour (primary actor, the goal, main-flow shape, which
   alternative/exception courses matter, business-rule thresholds/ordering/visibility, non-goals).
   Don't ask what the domain docs already answer. Keep it to a couple of focused rounds.

3. **Draft** from the template: actors, goal, pre/postconditions, a numbered **main flow**,
   **alternative/exception flows** as first-class citizens (anchored to main-flow steps), and
   **centralized business rules** referenced by id. Behaviour and business language only — if you write
   *how*, restate it as observable behaviour or a business rule. Put genuine unknowns in **Open
   questions**, not silent assumptions.

4. **Save** to `<use-cases>/UC-<n>-<slug>.md` (next number, zero-padded to three digits). Show the user
   the draft and the path.

   **Update the backlog** if `BACKLOG.md` exists. For an entry, append
   ` — written: [UC-<n>](<use-cases>/UC-<n>-<slug>.md)` to its first line; leave its box unticked and
   change nothing else. For an idea with no entry, ask whether to add it and in which section (MVP,
   Increments or Later); if yes, add it with the next free `B-<n>` id and recount that section's
   heading. Never add it without asking. If the entry's first line isn't in the expected format, say
   so and leave the file alone.

5. **Flag domain gaps.** If the use case needed a term, actor or rule missing from the domain docs, tell
   the user and offer to add it to the relevant file.

6. Remind the user they can send it through the pipeline with
   `/sdlc-pipeline:build-use-case <path-to-use-case>` once they have approved it, and that any Open
   questions left in it will come back to them at Gate 1.

For non-interactive drafting, the `sdlc-pipeline:use-case-writer` agent does the same job in one shot
(it lists questions instead of asking them live).
