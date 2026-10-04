## 1. Standards catalogue

- [x] 1.1 Write `templates/standards/architecture/layered.md`: six to eight `## §<n>` rules, each with `Why:`, `Check:` and `Profile:` lines (design D3), stack details as `<angle-bracket>` blanks. Verify by reading it against the "Good standards are" list in `docs/domain-and-standards.md`
- [x] 1.2 Write `templates/standards/architecture/hexagonal.md` in the same format. Verify every rule's `Check` names something a reviewer can see in code or a plan
- [x] 1.3 Write `templates/standards/concerns/testing.md` in the same format. Verify at least one rule targets `verification` and one targets `plan-review`
- [x] 1.4 Write `templates/standards/concerns/api.md`, with contract-first and code-first as two alternative rules marked so the user keeps at most one. Verify the alternatives are labelled as such
- [x] 1.5 Write `templates/standards/concerns/persistence.md`, including the additive-migrations rule. Verify no rule names a migration tool or database engine; they appear only as blanks

## 2. Catalogue validation

- [x] 2.1 Extend `scripts/validate.py` to check every `## §<n>` rule in `templates/standards/**/*.md` has `Why:`, `Check:` and `Profile:` lines, and that `Profile` values are only `implementation-rule`, `plan-review`, `verification` or `code-review`. Fail with the template and rule named. Verify by temporarily deleting a `Check:` line and seeing the script exit non-zero, then restoring it
- [x] 2.2 Add a short, case-insensitive, whole-word denylist of common languages, build tools and frameworks, and fail when a template contains one, naming the template and word. Verify by temporarily adding a framework name to a template and seeing the script fail, then removing it
- [x] 2.3 Run `python3 scripts/validate.py` on the finished catalogue and verify it passes (Python 3.8+, standard library only)

## 3. write-domain skill

- [x] 3.1 Write `skills/write-domain/SKILL.md` with a trigger description and `argument-hint`, matching `write-use-case`'s style. It reads the profile for the domain path, mines code, README, `CLAUDE.md`, docs and use cases, and drafts the five files with `(to confirm)` marks (spec: drafts the five domain files). Verify the frontmatter passes `python3 scripts/validate.py`
- [x] 3.2 Add the interview: `AskUserQuestion` in the order overview, actors and personas, glossary, bounded contexts, business rules; skip what sources already state (spec: interviews in dependency order). Verify by reading the steps against the spec scenarios
- [x] 3.3 Add re-run behaviour: read existing files, propose additions, confirm before writing, keep `BR-<AREA>-<n>` ids and take the next free number, never delete unasked (specs: stable ids, re-runs). Verify against the re-run scenarios
- [x] 3.4 Add the business-level rule, pointing to the "What to leave out" section of `docs/domain-and-standards.md` instead of copying it. Verify the skill names no stack

## 4. write-standards skill

- [x] 4.1 Write `skills/write-standards/SKILL.md` with a trigger description. It reads the profile (stopping with a pointer to `init` if it is missing), lists the catalogue under `${CLAUDE_PLUGIN_ROOT}/templates/standards/`, and asks for one architecture template and any concern templates. Verify the frontmatter passes `python3 scripts/validate.py`
- [x] 4.2 Add the keep/adapt/drop pass: one `AskUserQuestion` round per template, the "would you reject a change that broke this?" question for each rule, brownfield evidence shown as preselection only, and a check that adapted rules still have a reason and a check (design D4). Verify against the spec's keep/adapt/drop and existing-practice scenarios
- [x] 4.3 Add writing `standards/<template>.md` (architecture to `architecture.md`): fill blanks, number `§1…§n`, append with the next free number on re-run, never renumber. Verify against the blank-filled and re-run scenarios
- [x] 4.4 Add the profile update (design D5): one citing line per kept rule in each section its `Profile` names, matching existing lines by cited file and section, touching only lines that cite `standards/`, showing the full diff and writing only on confirmation. Verify against the four profile scenarios in the spec

## 5. init

- [x] 5.1 Replace step 4 of `skills/init/SKILL.md` with the wording in design D6. Verify the old "offer to draft a skeleton" text is gone and both skills are named

## 6. Docs, changelog and version

- [x] 6.1 Rewrite the "Creating them" section of `docs/domain-and-standards.md` around `write-domain` and `write-standards`, including the catalogue, keep/adapt/drop and the profile diff; update the `init` row of the agent table. Keep the manual prompts as a fallback. Verify every link still resolves
- [x] 6.2 Add both skills to the README's skills table and update the "Domain and standards" paragraph. Verify the table lists six skills
- [x] 6.3 Add a `[0.3.0]` entry to `CHANGELOG.md` saying host projects need do nothing, and bump the version to `0.3.0` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Verify the two versions match

## 7. Verification

- [x] 7.1 Run `python3 scripts/validate.py` and `claude plugin validate .` and verify both pass
- [ ] 7.2 In a brownfield host project with no `domain/` or `standards/`, run `claude --plugin-dir <this repo>`, then `/sdlc-pipeline:init`, `/sdlc-pipeline:write-domain` and `/sdlc-pipeline:write-standards`. Check that: `init` suggests both skills and creates neither folder; the domain files use the project's terms with `(to confirm)` on inferred entries and no implementation detail; questions follow the dependency order; dropped rules are absent from `standards/`; no stack blank is left unfilled; the profile diff touches only `standards/` citations and declining it leaves the profile unchanged
- [ ] 7.3 Re-run both skills in the same host project, adding one business rule and one standard. Check that existing `BR-` ids and `§` numbers are unchanged, the new ones take the next number, and the profile gains no duplicate lines
- [ ] 7.4 Run `/sdlc-pipeline:write-use-case` in that project and check the use case uses glossary terms and cites `BR-` ids from the new `domain/`
