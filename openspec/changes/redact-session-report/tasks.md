# Tasks

## 1. Secret and email redaction at load time

- [x] 1.1 Add the ordered `(kind, regex, replacement)` pattern table from design D3 and a `redact(text, counts)` function to `skills/session-report/session_report.py`. Verify that a new `test_redaction` in `selftest.py` checks one planted sample per kind becomes `[REDACTED:<kind>]`, the scheme word and assignment names are kept, and running `redact` a second time changes nothing.
- [x] 1.2 Add near-miss cases to `test_redaction` that must stay unchanged: `token = $TOKEN`, `password: <your password>`, a 40-hex git SHA, a UUID, the skill name `sk-reviewer`, and a short `Bearer x`. Verify that `python3 skills/session-report/selftest.py` passes.
- [x] 1.3 Make `load_events` walk every string in each parsed event and call `redact`, skipping `signature` and image `data` fields. Thread one `Counter` from `analyze_session` through the main and subagent loads, and store it as `data["redactions"]`. Verify with a fixture session in `selftest.py` that plants a bearer token in a Bash command, a private-key block in a prompt, an `export …_SECRET_KEY=` in a subagent transcript, an API key in a skill's args, and an email in an agent result. Check `data["redactions"]` has those counts.
- [x] 1.4 Add the redaction note from design D5 to `data["notes"]` and to the printed one-line summary. Verify the fixture's report notes and the summary's `notes` contain `redacted N values: …`, and that the clean fixtures A, B and C show no redaction note.

## 2. Home paths and the final check at output time

- [x] 2.1 Add the home-directory pass from design D2, covering `/home/<user>`, `/Users/<user>` and `C:\Users\<user>`, including text truncated mid-path. Apply it to the rendered HTML, the summary JSON string, the `--summary` printout and the compare report. Verify in `selftest.py` that a fixture with `cwd` `/home/alice/proj` produces outputs that never contain `alice`, and that Files touched still shows `src/app.ts`.
- [x] 2.2 Rework `write_outputs` and the compare path so both outputs are rendered into memory and checked before either is written (design D4). The check runs `html.unescape` on the HTML, scans with every pattern except `email`, and finds the section from the last `<h2>` or the top-level JSON key. Verify in `selftest.py` that, when the token is fed straight into the output rather than through the transcript, no file exists afterwards, the message names the kind and section but not the value, and the exit status is 1. Run it as a subprocess, the way the existing tests run the CLI.
- [x] 2.3 Verify end to end with the redaction fixture: grep the written `.report.html` and `.summary.json` for each planted value and for its first 8 characters. Every grep must find nothing.

## 3. Docs, skill wording and release

- [x] 3.1 Update `skills/session-report/SKILL.md` step 2 with the wording in design D6, and add a "Safe to commit" section to `skills/session-report/README.md`. The section lists what is redacted, what is not (secrets with no recognisable shape), the refusal and its exit status, and the redaction note. Verify the README's kinds match the pattern table.
- [x] 3.2 Add one line about redaction where the docs tell people to commit the report: `docs/pipeline.md` (session report bullet), `docs/evaluating-the-pipeline.md` (the session-report intro) and the `session-report` row in `README.md`. Verify with `grep -n "redact" README.md docs/*.md`.
- [x] 3.3 Add a `## [0.10.0]` entry to `CHANGELOG.md`. It covers redaction, the refusal, host action (none) and the advice to regenerate old reports. It also covers the "Skills used" section and the summary's `skills` field, which merged after 0.9.0. Bump `version` to `0.10.0` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`, and verify with `grep -n '"version"' .claude-plugin/*.json`.

## 4. Integration checks

- [x] 4.1 Time the generator on the largest local session log, before and after the change. Verify the run time is no more than about 2× the old time, and record both numbers in the PR. (Measured 0.24 s → 0.65 s on 21 MB, about 2.7×; accepted by the user, see design.md Risks.)
- [x] 4.2 Regenerate reports for three real sessions under `~/.claude/projects`. Verify each one writes, prints a sensible redaction note, and has no `/home/` or `/Users/` path left in either output.
- [x] 4.3 Run `python3 scripts/validate.py` and `claude plugin validate .`, and verify both pass.
- [x] 4.4 In a host project, run `build-use-case` once with `claude --plugin-dir <this repo>`. During the run, paste a fake token in a prompt (for example `ghp_` followed by 36 letters). Verify that the generated report and summary show `[REDACTED:github-token]`, that the retrospective's front matter still fills from the summary, and that Gate 2 and the commit reminder are unchanged.

## Workflow follow-up

- Archive the change once the PR is merged.
