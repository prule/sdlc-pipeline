# Proposal

## Why

Retrospectives find problems, but their recommendations are rarely adopted. A review of 15 runs in
one host project counted about 120 recommendations and 5 adopted rules; the same findings recurred
in up to 13 records. Each record repeats the earlier text with a `recurs:` list, and nothing makes
a recurring lesson come up before the next run. The host project fixed this by hand with a
`retrospectives/LEDGER.md`: one line per open or recurring recommendation, with a record count and
a limit of 3 records. The orchestrator should keep that ledger, so no one has to.

## What Changes

- New template `templates/ledger.md`: rules plus empty *Open* and *Closed* tables (id, recommendation,
  target, records, status).
- `build-use-case` step 0 reads the ledger's open lines and briefs the architect, and later agents,
  on the lines that apply to the use case.
- Gate 1 lists the applying *due* lines (3+ records). The human adopts each in the run, or gives a
  reason to keep it open or close it.
- Step 7 matches each recommendation to a ledger line: +1 to *Records*, `· ledger: L-<n>` in the
  record. New open recommendations get new lines. Gate 1 answers move lines to *Closed*. A missing
  ledger is created from the template and seeded from the five most recent records. The ledger
  replaces the five-record `recurs:` scan.
- `init` creates `LEDGER.md` in a new retrospectives folder.
- Templates `retrospective.md` and `retrospectives-README.md`, docs `pipeline.md`,
  `observability.md`, `README.md`, and `CHANGELOG.md`.

## Capabilities

### New Capabilities
- `recommendation-ledger`: how the pipeline reads, shows and updates the host project's ledger of
  open and recurring retrospective recommendations.

### Modified Capabilities
None.

## Impact

- **Skills:** `skills/build-use-case/SKILL.md` (step 0, Gate 1, step 7), `skills/init/SKILL.md`.
- **Templates:** new `templates/ledger.md`; `templates/retrospective.md`,
  `templates/retrospectives-README.md`.
- **Docs:** `README.md`, `docs/pipeline.md`, `docs/observability.md`, `CHANGELOG.md`.
- **Manifests:** `plugin.json` and `marketplace.json` to 0.8.0.
- **Host projects:** nothing is required. The next run creates `LEDGER.md` if it is missing. A
  project that already has a ledger in this format keeps it.
- **Semver:** minor bump (0.7.0 → 0.8.0). It adds a new run behaviour and a new project file. No
  profile edit is needed.
