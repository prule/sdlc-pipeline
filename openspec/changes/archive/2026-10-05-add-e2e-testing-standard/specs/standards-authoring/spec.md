## MODIFIED Requirements

### Requirement: Catalogue offers architecture and concern templates
The plugin SHALL ship a read-only standards catalogue with two architecture templates (`layered`, `hexagonal`) and four concern templates (`testing`, `api`, `persistence`, `e2e-testing`). `write-standards` SHALL let the user choose at most one architecture template and any number of concern templates.

#### Scenario: Choosing templates
- **WHEN** the user runs `write-standards`
- **THEN** the skill offers `layered` and `hexagonal` as alternatives, and `testing`, `api`, `persistence` and `e2e-testing` as a multiple choice

## ADDED Requirements

### Requirement: E2E template applies the Screenplay pattern
The `e2e-testing` template SHALL define the Screenplay terms (Actor, Ability, Task, Interaction, Question) in its header, and its rules SHALL require that: e2e tests are written as an actor's goals in glossary terms; only Interactions touch the user interface; assertions go through Questions; tools are reached through Abilities; e2e tests cover use case main flows rather than every edge case; and element locators are defined in one place and found by accessible role or test id. The template SHALL name no tool; the browser tool and the Screenplay library SHALL be stack blanks.

#### Scenario: Project keeps the e2e rules
- **WHEN** the user picks `e2e-testing` in `write-standards`, keeps every rule, and answers that the project uses Playwright with Serenity/JS
- **THEN** `standards/e2e-testing.md` contains the kept rules with the blanks filled in as Playwright and Serenity/JS, and the profile cites each kept rule in the sections its catalogue entry names

#### Scenario: Template names a tool
- **WHEN** the `e2e-testing` template contains the word "Playwright"
- **THEN** `python3 scripts/validate.py` exits non-zero and names the template and the word
