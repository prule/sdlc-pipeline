## 1. Guide

- [x] 1.1 Write `docs/domain-and-standards.md` with sections for the domain docs (the five files, what each covers, a short example, what to leave out), standards docs (what a standard covers, numbered rules, suggested files, profile vs standards, what to leave out), how to create them (draft with Claude from the codebase with a sample prompt, `init`, growing them from domain gaps, architect tasks and retrospectives) and keeping them useful (Context ingestion panel). Verify that every agent or skill behaviour it describes matches `agents/*.md` and `skills/*/SKILL.md`, and that it names no language, framework or build tool.

## 2. Entry points

- [x] 2.1 Add a "Domain and standards" section to `README.md` after Prerequisites (what each folder is for, which agents read it, how to start, link to the guide), shorten the Prerequisites bullet to point at it, and add the guide to the Documentation list. Verify the links resolve.
- [x] 2.2 Link the guide from `docs/pipeline.md` (where it names `standards/` and `domain/`) and from the Paths section of `docs/profile.md`. Verify the links resolve.

## 3. Release

- [x] 3.1 Add a `[0.2.1]` entry to `CHANGELOG.md` under "Changed"/"Added" for the docs, noting host projects need do nothing.
- [x] 3.2 Bump `version` to `0.2.1` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
- [x] 3.3 Run `python3 scripts/validate.py` and `claude plugin validate .` and confirm both pass. No host-project run is needed: no behaviour changes.
