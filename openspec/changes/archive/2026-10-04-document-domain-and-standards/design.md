## Context

The README mentions `domain/` and `standards/` once, in Prerequisites. The detail of how they are
used is spread across agent and skill prompts:

- `use-case-writer` and `write-use-case` read all domain docs for language, actors, bounded context
  and business rules, and report "domain gaps".
- `architect` reads at least the glossary and business rules, applies the standards, and adds a task
  to record any new term or durable rule.
- `spec-reviewer` checks the plan against the glossary, business rules and bounded context, and
  against the profile's checklist, citing `standards/<file>.md §<n>`.
- `qa` and `senior-dev` cite `standards/<file>.md §<n>` in their findings, and their root causes can
  be "missing/unclear standard".
- `init` drafts the profile's Implementation rules, Task order and Review checklist from
  `standards/`, and offers to draft a domain skeleton.
- `templates/use-case.md` names `domain/actors-and-personas.md` and `domain/bounded-contexts.md`.
- `docs/evaluating-the-pipeline.md` and `session-report` score each doc's reads and citations.

The guide describes this behaviour as it is; it doesn't change it.

## Goals / Non-Goals

**Goals:**
- A reader can create a useful first `domain/` and `standards/` from the guide alone.
- Every claim about how an agent uses the folders matches the current prompts.

**Non-Goals:**
- Shipping templates for domain or standards files. That would be a plugin change (and `init`
  would need to copy them); worth a separate change if users ask.
- Changing what any agent reads.

## Decisions

- **Short README section plus a docs page**, not a long README section. The README is the entry
  point and already links out to `docs/` for each topic; the full guide with examples would double
  its length. The README section carries enough to act on (what, who reads it, how to start).
- **File names follow what the prompts already use**: `overview.md`, `glossary.md`,
  `business-rules.md`, `bounded-contexts.md`, `actors-and-personas.md`. The use-case template names
  two of these, so documenting other names would break those references.
- **Standards file names are suggestions** (for example `testing.md`, `architecture.md`,
  `api.md`, `persistence.md`). No prompt depends on a standards file name; the profile cites them.
- **Business rules get ids** (`BR-1`, …) because use cases reference rules by id. Standards get
  numbered sections because findings cite `§<n>`.
- **Examples use one neutral domain** (a small library or shop) and describe rules, not code, to
  stay stack-agnostic.
- **"How to create them" leads with asking Claude to draft from the codebase**, with a sample
  prompt, then review by hand. Most projects already have the knowledge in code, tickets and
  existing docs.

## Risks / Trade-offs

- [The guide drifts from the agent prompts] → Each "how the agents use it" claim cites the agent or
  skill by name, so a prompt change shows which doc line to update.
- [Users copy the examples verbatim] → Keep examples short and label them as illustrations.
