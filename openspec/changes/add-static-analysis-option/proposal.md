# Proposal

## Why

QA proves the change meets its spec with tests, but nothing in the pipeline catches the bugs, code
smells and security issues a static-analysis server finds. A project can append a scan to its
**Verify** command, but then every agent runs it on every change, which is slow (a scan takes a
minute or more) and makes the implementer chase findings before its work is checked. Teams want the
scan as one QA step that they can turn on, and that stays off unless they do.

## What Changes

- New profile setting **Static analysis** in the `## Pipeline` section of
  `.claude/sdlc-profile.md`. Its value is `off` or the command that scans the project and fails
  when the analysis server's quality gate fails, such as `sonar-check`. If the setting is missing,
  it is `off`, so the pipeline works as it does today.
- When the setting names a command, `qa` runs it once, after the **Verify** command passes, and
  pastes the output. Each issue the failed quality gate lists is a defect: QA reports NOT READY, and
  the issues go back to the implementer through the existing qa↔implementer fix loop. A scan that
  cannot run (server down, missing token) is an infra issue, reported once, not a defect.
- QA's report gains a **Static analysis** line: `off`, `passed`, `failed (<n> issues)` or
  `not run (<reason>)`. Gate 2 shows it with the QA evidence.
- Docs: `docs/profile.md`, `docs/pipeline.md`, `README.md`, `CHANGELOG.md`.

## Capabilities

### New Capabilities
- `static-analysis`: how a host project turns a static-analysis scan on as part of QA, and how QA
  and the gates treat its result.

### Modified Capabilities
- None.

## Impact

- **Agents:** `agents/qa.md` (run the scan, report its result, findings as defects).
- **Skills:** `skills/build-use-case/SKILL.md` (Gate 2 shows the static-analysis line). `init`
  needs no change: it copies the profile template, so new profiles get the setting, set to `off`.
- **Templates:** `templates/sdlc-profile.md` (new field in `## Pipeline`).
- **Docs:** `README.md`, `docs/pipeline.md`, `docs/profile.md`, `CHANGELOG.md`.
- **Manifests:** `plugin.json` and `marketplace.json` to 0.9.0.
- **Host projects:** nothing is required. To turn the scan on, add
  `**Static analysis:** \`<command>\`` to the profile's `## Pipeline` section. The command and the
  analysis server it talks to are the project's to provide.
- **Semver:** minor bump (0.8.0 → 0.9.0). It adds an optional profile setting and a new QA step.
  Nothing a host project already has stops working.
