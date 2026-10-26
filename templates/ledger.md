# Recommendation ledger

One line for each retrospective recommendation that is still open or that recurs. The run records
link here by id, so a lesson that comes back adds a count, not another copy of its text. The
`build-use-case` orchestrator reads this file at the start of a run and updates it at the end.

## Rules

- **At step 0 of a run:** the orchestrator reads the Open lines. It tells the architect about each
  line that applies to the use case, and tells later agents about the lines that apply to their
  phase. Gate 1 lists the *due* lines that apply.
- **After a run:** the orchestrator matches each recommendation in the new record to an Open line.
  For each match, it adds 1 to *Records* (once per record) and writes the ledger id in the record
  (`· ledger: L-8`). It adds a new line for a recommendation that is still open after its run.
- **Limit:** a line with 3 or more records is *due*. At Gate 1 the human adopts it in that run, or
  writes a reason to keep it open or to close it.
- **Adopting:** edit the target files in a PR, move the line to Closed with *Status*
  `adopted, #<PR>`, and tick the matching items in the records. A target in the plugin
  (an agent or skill) is adopted by an issue or PR in
  [`prule/sdlc-pipeline`](https://github.com/prule/sdlc-pipeline); put its link in *Status*.
- **Ids:** `L-<n>`, the next number after the highest in either table. An id is never reused.
- **Status:** `open`, `due` (3+ records), or a short note such as `kept: <reason>`. A closed line
  says `adopted, #<PR>` or `closed: <reason>`.

## Open

| Id | Recommendation | Target | Records | Status |
|---|---|---|---|---|

## Closed

| Id | Recommendation | Records | Status |
|---|---|---|---|
