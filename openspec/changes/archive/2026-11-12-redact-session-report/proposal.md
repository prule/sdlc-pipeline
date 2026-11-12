# Proposal

## Why

`build-use-case` tells the human to commit the session report and its `.summary.json` with
every change. Both files copy raw text from the transcript: your prompts, Claude's replies and
thinking, shell commands, agent results, error messages, skill args and absolute paths. If a
token, a private key, a password or an email reached the session, it ends up in git. Nothing
stops that today, so the report is not safe to commit by default.

## What Changes

- The session report redacts secrets before it writes anything. API keys and tokens (known
  vendor formats), private-key blocks, JWTs, bearer and basic auth headers, passwords in URLs,
  and `key/secret/token/password = value` style assignments become `[REDACTED:<kind>]`.
- It also removes personal data: email addresses become `[REDACTED:email]` and home-directory
  paths (`/home/<user>`, `/Users/<user>`, `C:\Users\<user>`) become `~`.
- Redaction covers every output: the HTML report, the `.summary.json`, the `--summary` printout
  and the `--compare` report.
- The run says what it redacted, as counts by kind and never the values. The counts go into
  the printed summary line and the report's notes.
- A final check scans each output file before it is kept. If a secret pattern still matches,
  the script deletes that output, names the kind and the place, and exits non-zero. A report
  that might leak is never left on disk.
- Not covered: secrets with no recognisable shape (for example a bare random string with no
  label next to it). The README says so and tells the reader to review the report before
  committing when the session handled credentials.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `session-report`: four new requirements. Secrets are redacted from every output. Personal
  data is removed from every output. Redactions are counted but never shown. A report that
  still matches a secret is not written.

## Impact

- **Skills:** `skills/session-report/session_report.py` gets the redaction, the final check
  and the counts. `skills/session-report/selftest.py` gets a fixture full of planted secrets.
  `SKILL.md` and `README.md` describe what is redacted and what is not.
- **Docs:** `docs/evaluating-the-pipeline.md` and any other page that tells people to commit
  the report gets a line on redaction. `CHANGELOG.md` gets an entry.
- **Manifests:** the version goes up in `plugin.json` and `marketplace.json`.
- **Agents, hooks, templates:** no change. `build-use-case` keeps telling people to commit
  the report. That instruction becomes safe, and its wording does not change.
- **Host projects:** nothing to do. Reports that are already committed are not rewritten. The
  CHANGELOG suggests that projects regenerate them if they are worried.
- **Not in scope:** `hooks/log-event.py` and `scripts/pipeline-report.py`. Those write the
  host's `logs/` event log and its dashboard, which are a separate output. Raw transcripts
  under `~/.claude` are never committed.
- **Semver:** minor, 0.9.0 → 0.10.0. This is new report behaviour that host projects can see,
  and they need do nothing. The "Skills used" section, which was merged after 0.9.0, ships in
  the same release.
- **Dependencies:** none. Standard-library `re` only.
