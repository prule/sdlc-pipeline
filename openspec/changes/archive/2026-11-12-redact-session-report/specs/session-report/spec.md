# Spec Delta

## ADDED Requirements

### Requirement: Secrets are redacted from every output
Before it renders anything, the session report SHALL replace each recognisable secret in the transcript text with `[REDACTED:<kind>]`. That covers vendor API keys and tokens, private-key blocks, JWTs, bearer and basic auth headers, passwords in URLs, and values assigned to a key, secret, token or password name. This SHALL hold for the HTML report, the summary file, the `--summary` output and the compare report.

#### Scenario: Token in a shell command
- **WHEN** an agent ran `curl -H "Authorization: Bearer <token>" …` during the session
- **THEN** the activity feed and every other output show `Authorization: Bearer [REDACTED:bearer]`, and the token appears in no output file

#### Scenario: Private key pasted in a prompt
- **WHEN** a prompt contains a full `-----BEGIN … PRIVATE KEY-----` block
- **THEN** the whole block, including the BEGIN and END lines, is replaced by `[REDACTED:private-key]` before any truncation, so no part of the key shows

#### Scenario: Secret in an environment assignment
- **WHEN** a command contains `export STRIPE_SECRET_KEY=sk_live_…` or a file edit contains `"password": "hunter2"`
- **THEN** the name stays and the value becomes `[REDACTED:…]`

#### Scenario: Secret in a subagent transcript
- **WHEN** a secret appears only inside a subagent's transcript, for example in its final result or a skill's args
- **THEN** it is redacted in the agent table, findings, skills section and summary, the same as a secret in the top-level session

### Requirement: Personal data is removed from every output
The session report SHALL replace email addresses with `[REDACTED:email]` and the home-directory part of any path with `~` (for example `/home/<user>/proj` becomes `~/proj`). This SHALL hold in every output, including the header's working directory and paths outside the project.

#### Scenario: Header working directory
- **WHEN** the session ran in `/home/alice/projects/app`
- **THEN** the report header shows `~/projects/app`, and `alice` appears in no output file

#### Scenario: Email in a commit trailer
- **WHEN** a commit message in the session contains `Signed-off-by: Alice <alice@example.com>`
- **THEN** the outputs show `Signed-off-by: Alice <[REDACTED:email]>`

#### Scenario: Project files stay readable
- **WHEN** files inside the project were read or edited
- **THEN** Files touched still lists them relative to the project root, the same as before

### Requirement: Redactions are counted, never shown
The session report SHALL report how many values it redacted, by kind, in its printed summary line and in the report's notes. It SHALL never print a redacted value or any part of one.

#### Scenario: Two kinds redacted
- **WHEN** the session contained one bearer token and three email addresses
- **THEN** the printed line and the report notes say `redacted 4 values: 1 bearer, 3 email`

#### Scenario: Nothing to redact
- **WHEN** the session contained no secret or personal data
- **THEN** no redaction note is shown

### Requirement: A report that still matches a secret is not written
After it renders each output, the session report SHALL scan that output for the secret patterns again. If any pattern still matches, it SHALL keep no output file from that run, print the kind and the section where the match was found (never the value), and exit non-zero.

#### Scenario: Leak caught by the final check
- **WHEN** a code path puts transcript text into an output without redaction, and that text holds a token
- **THEN** no report or summary file is left on disk, the error names the kind and the section, and the exit status is non-zero

#### Scenario: Clean run
- **WHEN** every secret was redacted
- **THEN** the report and the summary are written as usual and the exit status is zero
