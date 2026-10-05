---
name: write-domain
description: Build or grow the project's domain docs (overview, actors and personas, glossary, bounded contexts, business rules) by drafting from the code and docs, then interviewing the user to confirm and fill the gaps. Use when the user wants to create, write, draft or extend domain/ docs, a glossary or business rules, or when init reports the domain folder is missing.
argument-hint: "[area to focus on, e.g. \"loans and holds\"]"
---

Build the project's **domain docs**: what the business is, in its own words. They describe the
business, never the system built for it. Focus from the user, if any:

$ARGUMENTS

What belongs in each file, and what to leave out, is set by
`${CLAUDE_PLUGIN_ROOT}/docs/domain-and-standards.md` ("The domain docs"). Read it first and follow it.

## Steps

1. **Load context.** Read `.claude/sdlc-profile.md` for the domain path (default `domain/`; if the
   profile is missing, use the default and suggest `/sdlc-pipeline:init`). Read any domain files that
   already exist. The five files are `overview.md`, `actors-and-personas.md`, `glossary.md`,
   `bounded-contexts.md` and `business-rules.md`.

2. **Mine the sources.** Read the PRD (usually `docs/prd.md`) first, then the README, `CLAUDE.md`,
   the rest of `docs/`, existing use cases and
   `openspec/specs/`, then the code's names for things (types, modules, messages, error text). Draft
   every entry you can. Mark each entry you **inferred** rather than found stated as `(to confirm)`.
   Translate implementation into business terms: a `loans` table with a `due_date` column becomes a
   *Loan* with a *due date*. On a project with no code or docs, skip this step.

3. **Interview, in this order.** Each step gives you the words for the next, so don't jump ahead:

   ```
   overview --> actors and personas --> glossary --> bounded contexts --> business rules
   ```

   For each file, use `AskUserQuestion` to confirm the `(to confirm)` entries and fill the gaps.
   Show your draft entries as the options where you can; people correct a draft faster than they
   write from nothing. Don't ask about anything a source already states clearly. Ask in small
   batches (one file per round, a few questions each). Remove the `(to confirm)` mark from each entry
   the user confirms. Leave it on any the user skips.

   For the glossary, ask about synonyms to avoid ("we say *member*, not *user*"). For business rules,
   ask for the thresholds, orderings and exceptions; a rule without its numbers isn't checkable.

4. **Give every business rule an id** of the form `BR-<AREA>-<n>`, where `<AREA>` is a short
   upper-case name for the part of the business (`BR-LOAN-1`). Existing ids never change. A new rule
   takes the next free number in its area. Never reuse a deleted rule's id.

5. **Write.** If a file doesn't exist, show the user the draft and write it. If it exists, show the
   additions and changes as a diff and write only after the user confirms. Never delete or rewrite an
   existing entry unless the user asks to.

6. **Report** the files written, the entries still marked `(to confirm)`, and any questions the user
   deferred. Suggest the next step: `/sdlc-pipeline:write-standards` if the project has no
   `standards/`. Otherwise, suggest updating `openspec/config.yaml` and the README to point at the
   domain and standards docs (see `${CLAUDE_PLUGIN_ROOT}/docs/getting-started.md`, step 5), then
   `/sdlc-pipeline:write-use-case <idea>`.

## Rules

- **Business level only.** No tables, columns, endpoints, classes, screens, protocols or
  technologies. If you catch yourself writing *how*, restate it as what the business does.
- **Don't invent policy.** A threshold, ordering or eligibility rule you can't find stays a question
  for the user, not a plausible default.
- **One meaning per term.** If the sources use two words for one thing, or one word for two things,
  ask which the business means. Different meanings in different parts of the business are a sign of
  separate bounded contexts.
