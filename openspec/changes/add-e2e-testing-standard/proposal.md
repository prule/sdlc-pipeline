## Why

The standards catalogue has no rules for end-to-end tests. Teams that test web UIs through the
Screenplay pattern (Actors, Abilities, Tasks, Interactions, Questions) have nothing to start from in
`write-standards`. Without rules, reviewers can't flag the usual failures: tests written as clicks
and selectors, assertions that query the page directly, and an e2e suite that tries to cover every
edge case. The pattern itself names no tool, so it can sit in the stack-agnostic catalogue. The
tools (such as Playwright and Serenity/JS) are filled in by the project's interview.

## What Changes

- New concern template `templates/standards/concerns/e2e-testing.md`. Its header comment defines
  the Screenplay terms in a few lines. It then lists six to eight checkable rules: tests are written
  as the actor's goals in glossary terms; Tasks are built from Interactions and only Interactions
  touch the UI; assertions go through Questions; tools are reached through Abilities; e2e tests
  cover use case main flows, not every edge case; locators are defined in one place and found by
  accessible role or test id. Tools are stack blanks such as `<e2e browser tool>` and
  `<screenplay library>`.
- `scripts/validate.py`: the stack-name list gains common e2e tools (`playwright`, `serenity`,
  `cypress`, `selenium`, `webdriverio`, `puppeteer`), so a template can't name them.
- `write-standards` needs no change. It lists whatever the catalogue holds, so the new template
  appears as a fourth concern.
- Docs: the catalogue table in `docs/domain-and-standards.md` and the "Typical rules" table list
  e2e testing. CHANGELOG entry.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `standards-authoring`: the catalogue requirement changes from three concern templates to four,
  adding `e2e-testing`.

## Impact

- **Components:** templates (new `concerns/e2e-testing.md`), scripts (`validate.py`), docs
  (`docs/domain-and-standards.md`), manifests and `CHANGELOG.md`. No agent or skill prompt changes.
- **Host projects:** need do nothing. A project that wants the rules runs
  `/sdlc-pipeline:write-standards` again and picks `e2e-testing`. Its existing standards and profile
  are untouched until it does.
- **Semver:** minor bump to 0.4.0. It adds a new catalogue template, which is new user-facing
  content. Nothing existing changes.
