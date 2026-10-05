## 1. Validator

- [x] 1.1 Add `playwright`, `serenity`, `cypress`, `selenium`, `webdriverio` and `puppeteer` to `STACK_NAMES` in `scripts/validate.py` (design D5). Verify by temporarily adding "Playwright" to a catalogue template and seeing the script exit non-zero naming the template and `playwright`, then removing it

## 2. E2E template

- [x] 2.1 Write `templates/standards/concerns/e2e-testing.md` with the catalogue header comment, plus one line each defining Actor, Ability, Task, Interaction and Question (design D3). Verify the definitions name no tool
- [x] 2.2 Add the three general rules first, then the four Screenplay rules (design D2): main flows only; locators in one place by accessible role or test id; known starting state; tests as Tasks named for the actor's goals in glossary terms; only Interactions touch the UI; assertions through Questions; tools only through Abilities. Each has `Why:`, `Check:` and `Profile:` per design D4, with tools as blanks (`<e2e browser tool>`, `<screenplay library>`, `<e2e test location>`, `<test id attribute>`). Verify no rule refers to another rule or to `testing.md` by number
- [x] 2.3 Run `python3 scripts/validate.py` and verify it passes with the new template

## 3. Docs, changelog and version

- [x] 3.1 In `docs/domain-and-standards.md`, add `e2e-testing` to the Concerns row of the catalogue table and an `e2e-testing.md` row to the "Typical rules" table. Verify both tables render and list it
- [x] 3.2 Add a `[0.4.0]` entry to `CHANGELOG.md` saying host projects need do nothing and how to adopt the template (re-run `write-standards`), and bump the version to `0.4.0` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Verify the versions match

## 4. Verification

- [x] 4.1 Run `python3 scripts/validate.py` and `claude plugin validate .` and verify both pass
- [x] 4.2 In a host project with a web UI, run `claude --plugin-dir <this repo>` and `/sdlc-pipeline:write-standards`, picking `e2e-testing` and answering Playwright and Serenity/JS. Check that: the template is offered as a concern alongside `testing`, `api` and `persistence`; `standards/e2e-testing.md` contains only the kept rules with no `<blank>` left; the profile diff adds a citing line for each kept rule in the sections its `Profile` names and nothing else changes
