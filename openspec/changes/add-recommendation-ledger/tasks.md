# Tasks

## 1. Template

- [x] 1.1 Add `templates/ledger.md` with the rules (step 0, after a run, limit, adopting, ids, status) and empty Open and Closed tables, based on the host project's ledger; verify it names no stack.

## 2. Orchestrator

- [x] 2.1 In `skills/build-use-case/SKILL.md` step 0, read the ledger's Open lines, brief the architect and later agents on the applying lines, and note the due ones (design D3).
- [x] 2.2 Add `Due ledger lines` and the adopt / keep / close question to Gate 1 (design D2).
- [x] 2.3 Replace the step 7 recurrence scan with the ledger update, seed a missing ledger from the five most recent records, add ledger counts to the status line and `LEDGER.md` to the commit reminder (design D1); verify against the spec scenarios.

## 3. Init, templates, docs, changelog and version

- [x] 3.1 In `skills/init/SKILL.md`, create `LEDGER.md` beside the retrospectives README.
- [x] 3.2 Update `templates/retrospective.md` (recommendations end with `· ledger: L-<n>`) and `templates/retrospectives-README.md` (a ledger section; Using them).
- [x] 3.3 Update `docs/pipeline.md` (Retrospectives), `docs/observability.md` (tool table) and `README.md` (templates line).
- [x] 3.4 Add a `## [0.8.0]` entry to `CHANGELOG.md` and bump both manifests to `0.8.0`.

## 4. Verification

- [x] 4.1 Run `python3 scripts/validate.py` and `claude plugin validate .`; both pass. (`claude plugin validate .` runs in CI.)
- [ ] 4.2 In a host project with a ledger, run `claude --plugin-dir <this repo>` and `/sdlc-pipeline:build-use-case <use case>`. Check: the architect's prompt has `Ledger lessons`; Gate 1 lists the due lines; the record's recommendations end with `· ledger:` ids; matched lines gained 1; new lines have the next id; the commit reminder names `LEDGER.md`.
- [ ] 4.3 In a host project with records and no ledger, run once. Check `LEDGER.md` is created and seeded with the recurring recommendations.
