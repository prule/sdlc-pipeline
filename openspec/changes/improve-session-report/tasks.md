## 1. Self-test and fixtures

- [x] 1.1 Build three small synthetic sessions (main `.jsonl` plus `subagents/`) in the self-test, written to a temp folder at run time rather than committed, as in design D9: (a) a resumed junior-dev with `meta.json` files, a qa findings block handing back Q1–Q3, a resume, and a re-verify; (b) the same shape with no `meta.json` files and no resume markers; (c) a session with `cat standards/testing.md`, a `tool-results/` read and a Gate 1 `AskUserQuestion` wait. Use invented content only, never a real transcript. Verify each file parses with `load_events()`
- [x] 1.2 Write `skills/session-report/selftest.py` (standard library only) that runs the analysis on each fixture and asserts the spec scenarios. It should fail before the later tasks are done. Verify it runs and reports which assertions fail
- [x] 1.3 Make `scripts/validate.py` run the self-test and fail when it fails. Verify by breaking one expected value temporarily

## 2. Linking and per-run work

- [x] 2.1 Read `agent-<id>.meta.json` in `load_subagents()` and link runs by `toolUseId` in `link_subagents()`, falling back to the prompt; record `linked_by` per run (design D1). Verify the fixture (a) links by id and (b) by prompt
- [x] 2.2 Split each agent's transcript by its runs' start times (design D2), computing tool calls, tokens, files, context signals and duration per segment; cross-check against resume markers and record a note on mismatch or missing start times. Verify the fixture (a) fix run has its own tool count and the first run excludes it, and (b) falls back with a note

## 3. Shell access and files

- [x] 3.1 Add the shell command parser (design D3) and feed its reads and writes into the context and file aggregates, labelled "incl. shell". Verify fixture (c) counts a read of `standards/testing.md`
- [x] 3.2 Drop Claude Code's own files from the files panel and show paths relative to the project root. Verify fixture (c) shows no `tool-results/` path and the logbook-style paths are relative

## 4. Findings, fix loops, time and tokens

- [x] 4.1 Parse Run-log findings blocks from gate results (design D4), derive verdicts from them, mark keyword verdicts as inferred, and pick the snippet from the verdict line or first finding. Verify fixture (a) yields Q1–Q3 with their fields, and a block-less gate shows an inferred verdict
- [x] 4.2 Build fix loops from the run sequence (design D5) with their cost, including loops not re-checked. Verify fixture (a) has one qa loop listing Q1–Q3 with the fix and re-verify runs
- [x] 4.3 Compute the time breakdown (design D6). Verify fixture (c) counts the Gate 1 wait as human time and that agents, human and orchestrator add up to wall time
- [x] 4.4 Total input, cache-write, cache-read and output tokens per run, per agent type and for the session. Verify the fixture totals match the hand-computed sums

## 5. Summary file

- [x] 5.1 Extend `run_summary()` to the shape in design D7 (existing fields unchanged, `schema: 1`), write `<session>.summary.json` beside the report on every run, and print the same object with `--summary`. Verify the self-test checks the printed and written objects are identical, and that a session with no agents gives empty `runs` and `fix_loops`

## 6. Layout

- [x] 6.1 Reorder `render()` and the HTML template as in design D8: header with use case and change, new cards, findings table, agent table with token columns, context, then errors, tools, files and feed in closed `<details>`. Verify by opening a fixture report and checking the order and that diagnostics start closed
- [x] 6.2 Rework the timeline into one lane per agent type with a "you" lane for human waits and fix-loop brackets, keeping `--compact` and both themes. Verify on fixture (a) that resumed runs share a lane and the loop bracket spans the qa run to the re-verify
- [x] 6.3 Show the linking and fallback notes from 2.1 and 2.2 in the report. Verify on fixture (b)

## 7. build-use-case, docs, changelog and version

- [x] 7.1 Replace the commit reminder in `skills/build-use-case/SKILL.md` with the wording in design D10. Verify the old sentence is gone
- [x] 7.2 Update `skills/session-report/README.md` (report anatomy, the summary file and its fields, the fallbacks), `skills/session-report/SKILL.md` (summary file, where to look for fix loops and findings), `docs/observability.md` and the README's quick start (the `.summary.json` file). Verify every link resolves
- [x] 7.3 Add a `[0.5.0]` entry to `CHANGELOG.md` saying host projects need do nothing and should commit the new summary file with each report; bump `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` to `0.5.0`. Verify the versions match

## 8. Verification

- [x] 8.1 Run `python3 scripts/validate.py` (including the self-test) and `claude plugin validate .` and verify both pass
- [x] 8.2 Regenerate reports for the logbook `47d3f4bc…` and sdlc `4ef81b30…` transcripts into the scratchpad and compare with the old reports. Check: the context panel no longer lists docs as never read when agents read them with `cat`; each resumed run shows its own work; the findings table lists the gates' P, Q and C findings; fix loops match the run's real loops; the human-wait time is plausible against the gate questions
- [ ] 8.3 In a host project, run `/sdlc-pipeline:build-use-case` with `claude --plugin-dir <this repo>` on a small use case. Check that `reports/sessions/` gains both the HTML report and the `.summary.json`, the retrospective front matter is filled as before, and the commit reminder names the summary file
