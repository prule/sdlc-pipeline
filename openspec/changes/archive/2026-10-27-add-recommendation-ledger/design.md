# Design

## Context

The format and rules come from a host project's hand-kept `retrospectives/LEDGER.md`, which is the
agreed design. This change makes the orchestrator do the two steps the human did by hand: read the
ledger before planning, and update it after the run.

## Decisions

### D1 — The ledger replaces the five-record recurrence scan

Current step 7 wording:

> **Recurrence:** before writing, read the five most recent records in the retrospectives
> directory. Mark any finding or recommendation that appeared before with `recurs: <earlier file>`.

Replacement: match each recommendation to an open ledger line and write `· ledger: L-<n>`. The
ledger's *Records* count is a better recurrence signal than a five-record window: it covers every
run, and lines that recur in run 1 and run 9 still meet. The five-record scan is kept only to seed
a ledger that is missing, so a project with records and no ledger starts with its recurring lessons
instead of an empty table.

Failure it fixes: the same finding recurred in up to 13 records, each time as text with a
`recurs:` list, and was not adopted.

### D2 — Due lines are a Gate 1 decision

Adopting a due line edits an input (a standard, the profile, `openspec/config.yaml`), which is
scope beyond the use case. The budget rule "no silent scope growth" applies, so the orchestrator
does not adopt lines itself. It lists them at Gate 1 and the human chooses adopt, keep (with a
reason) or close (with a reason). A plugin target is adopted by an issue here, not in the run.

### D3 — Briefing stays tight

Step 0 passes only the lines that apply, with their ids, and gives later agents only the lines for
their phase. This follows the existing rule to keep each subagent's context tight.

## Stack-agnostic and OpenSpec

The ledger names no language or tool; its targets are whatever files the host project uses. The
change touches only the orchestrator's bookkeeping, not OpenSpec's workflow or artifacts.
