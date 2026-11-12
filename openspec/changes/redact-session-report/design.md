# Design

## Context

`session_report.py` reads transcripts in one function, `load_events`. It is called for the main
log and for each subagent log, and `--compare` reaches it through `analyze_session`. Text then
flows into four outputs: the HTML report (through `render` and `esc`), the summary file (through
`run_summary`), the `--summary` printout and the compare report. Many render paths truncate text
first, to 120–600 characters. `relative_files` already shortens home paths to `~`, but only in
Files touched. The header's working directory, the feed, error text and the skills args still
show full paths. Nothing redacts secrets. Python is 3.8+ with the standard library only.

## Goals / Non-Goals

**Goals:**
- One redaction point that every output inherits, including outputs added later.
- No partial secret survives truncation.
- A final check that makes a missed code path fail loudly instead of leaking quietly.

**Non-Goals:**
- Entropy-based detection of unlabelled random strings. It flags hashes, ids and base64
  fixtures, and the noise would hide real findings.
- A `--no-redact` flag or extra patterns set in the profile. Anyone who needs raw text has
  the raw transcript. Patterns set in the profile would mean a profile change, so they can
  wait until someone asks.
- Rewriting reports that are already committed, the host's `logs/pipeline-events.jsonl`, or
  the `pipeline-report.py` dashboard.

## Decisions

**D1. Redact secrets and emails at load time, inside `load_events`.** After each line is parsed,
walk every string value in the event and replace matches. Every later step, every output and
every subagent then sees only redacted text. Because this happens before any truncation, a
private key can't be cut in half and leave its first 200 characters visible. Skip the fields
that are never rendered and hold large opaque blobs: thinking `signature` and image `data`.
This is for speed, not safety. `analyze_session` creates a `Counter`, passes it to each
`load_events` call (main and subagents) and stores it as `data["redactions"]`.
*Alternative considered:* redact in `esc()` and in `run_summary`. That was rejected for two
reasons. It runs after truncation, so a partial key leaks. And every new output would need to
remember to call it.

**D2. Shorten home directories at output time.** After rendering, run one pass over the final
HTML and JSON strings that replaces `/home/<user>`, `/Users/<user>` and `C:\Users\<user>`
with `~`. A pass at load time would break things that compare paths to the session's
absolute `cwd`, such as `relative_files` and the context docs, which are matched as paths
relative to the project. A pass over the finished string can't break that logic. It also
catches every place a path ends up, including text truncated mid-path (`/home/al…` becomes
`~…`). `relative_files` keeps its own shortening, so it doesn't need to change.

**D3. Ordered, named patterns.** Use a list of `(kind, compiled regex, replacement)` entries,
most specific first, so a vendor token is labelled by its vendor before the generic
assignment rule can catch it:

| Kind | Shape |
|---|---|
| `private-key` | `-----BEGIN [A-Z ]*PRIVATE KEY-----` … `-----END … -----` (DOTALL). If the text was cut and the END line is missing, match to the end of the string |
| `aws-key` | `\b(AKIA\|ASIA)[0-9A-Z]{16}\b` |
| `github-token` | `\bgh[pousr]_[A-Za-z0-9]{36,}\b`, `\bgithub_pat_[A-Za-z0-9_]{22,}` |
| `gitlab-token` | `\bglpat-[A-Za-z0-9_-]{20,}` |
| `slack-token` | `\bxox[abprs]-[A-Za-z0-9-]{10,}` |
| `stripe-key` | `\b[sr]k_(live\|test)_[A-Za-z0-9]{16,}` |
| `anthropic-key` / `openai-key` | `\bsk-ant-[A-Za-z0-9_-]{20,}`, then `\bsk-(proj-)?[A-Za-z0-9_-]{20,}` |
| `google-key` | `\bAIza[0-9A-Za-z_-]{35}` |
| `npm-token` | `\bnpm_[A-Za-z0-9]{36}` |
| `jwt` | `\beyJ[\w-]+\.eyJ[\w-]+\.[\w-]+` |
| `bearer` / `basic` | `(Authorization:\s*)?(Bearer\|Basic)\s+<token of 8+ chars>`. Keep the scheme word and replace the token |
| `url-password` | `scheme://user:<password>@`. Keep the user and replace the password |
| `assignment` | A name ending in `secret`, `token`, `passwd`/`password`, `api_key`/`apikey`, `access_key`, `private_key` or `credential(s)` (optionally followed by `_key`, as in `SECRET_KEY`), then an optional quote, `=` or `:`, an optional quote, and a value of 6+ characters that holds a letter and a digit or symbol. Keep the name and replace the value. Skip values that start with `$`, `<`, `{` or `[REDACTED`: these are references, placeholders or already redacted. *Tightened during implementation:* a first version matched any name containing `token`, which on real logs redacted only TypeScript code such as `tokens: number` and `tokenUsage: TokenUsage` |
| `email` | the usual `local@domain.tld` shape |

Every replacement is `[REDACTED:<kind>]`, and no pattern matches that text, so running the
redaction twice changes nothing. That matters for D4.

**D4. The final check runs on the rendered strings, before anything is written.**
`write_outputs` renders the HTML and the summary JSON into memory and applies D2. It runs
`html.unescape` on the HTML, because `esc` turns `"password": "x"` into `&quot;…`, which hides
the quotes the patterns key on. Then it scans both strings with the D3 patterns, except
`email`. Once the redaction has run, any address left in the output is one of the tool's own
fixed strings, not data from the session. On any match it writes nothing, prints
`refusing to write report: <kind> found in <section>` and exits 1. The section is the last
`<h2>` before the match in the HTML, or the top-level key in the summary. Only when both
strings are clean are both files written. The compare report and the `--summary` printout go
through the same check. Checking in memory instead of writing and then deleting means a crash
between the two steps can't leave a leaking file behind.

**D5. Counts are reported, never values.** When `data["redactions"]` is non-empty,
`analyze_session` adds a note: `redacted N values: 1 bearer, 3 email`, ordered by kind. The
note appears in the report's notes list and in the summary's `notes`, so the build-use-case
retrospective can see it. The printed one-line summary gets the same text. Home-path
shortening is not counted. It is formatting, not removal of a secret.

**D6. One line added to SKILL.md.** The current wording in step 2 is: "The report and its
summary file are meant to be committed with the change they describe." Proposed replacement:
"The report and its summary file are meant to be committed with the change they describe.
The script redacts secrets and personal data before writing. If it refuses to write because a
secret survived, tell the user which section it named; never work around it by editing the
output or the script." This prevents the failure where an agent edits the output by hand to
"fix" a refused write. No retrospective has recorded that failure yet. It closes the gap
before one does.

**Stack-agnostic, OpenSpec untouched.** The patterns describe credential formats, not the host
project's language or build tool. Nothing in agents, templates or the OpenSpec workflow
changes.

## Risks / Trade-offs

- [A secret with no recognisable shape, such as a bare password typed in a prompt, passes
  through] → The README states the limit plainly and says to review the report before
  committing when a session handled credentials.
- [False positives: code like `token = request.headers["x"]` loses its value in the feed] →
  Acceptable. The report is a diagnostic, and the redacted kind still shows what was there.
- [The final check fires on a pattern match that isn't really a secret, and blocks the
  report] → The error names the section, so the pattern can be tuned. The self-test fixture
  pins both the matches and the near-misses that must not match.
- [Slower on large logs] → The patterns are compiled once and blob fields are skipped. Each
  pattern runs only on strings that contain one of its literal triggers, found with a single
  compiled regex. The nested payloads of events the analysis never reads (API request blobs,
  file snapshots) are dropped before redaction. Measured on the largest local log (21 MB):
  0.24 s before, 0.65 s after. That is about 2.7×, above the 2× first planned. The remainder
  is one scan over about 10 MB of text, which redaction can't skip.
- [Vendor token formats change] → Each pattern is one table row. The fixture shows which
  ones to update.

## Migration Plan

No host action. The next report generated is redacted. Rollback is a revert of the release.
The CHANGELOG suggests regenerating committed reports from their transcripts, if they are still
under `~/.claude/projects`, for any project that is worried about past runs.
