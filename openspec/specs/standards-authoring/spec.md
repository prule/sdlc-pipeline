# standards-authoring Specification

## Purpose

The `write-standards` skill turns templates from the plugin's standards catalogue into a host project's own `standards/` docs, keeping only the rules the team will enforce, and wires the kept rules into the profile so the agents read them.

## Requirements

### Requirement: Catalogue offers architecture and concern templates
The plugin SHALL ship a read-only standards catalogue with two architecture templates (`layered`, `hexagonal`) and three concern templates (`testing`, `api`, `persistence`). `write-standards` SHALL let the user choose at most one architecture template and any number of concern templates.

#### Scenario: Choosing templates
- **WHEN** the user runs `write-standards`
- **THEN** the skill offers `layered` and `hexagonal` as alternatives, and `testing`, `api` and `persistence` as a multiple choice

### Requirement: Catalogue rules are complete and stack-agnostic
Every rule in a catalogue template SHALL be numbered and SHALL state its reason, its check and the profile sections that cite it. A template SHALL NOT name a language, build tool or framework; stack-specific details SHALL appear as blanks in angle brackets. `scripts/validate.py` SHALL fail when a rule is missing its reason, check or profile sections, when a profile section name isn't one of `implementation-rule`, `plan-review`, `verification` or `code-review`, or when a template contains a name from its list of common languages, build tools and frameworks.

#### Scenario: Rule without a check
- **WHEN** a catalogue rule has a reason and profile sections but no check
- **THEN** `python3 scripts/validate.py` exits non-zero and names the template and rule

#### Scenario: Template names a framework
- **WHEN** a catalogue template contains a framework name on the validator's list
- **THEN** `python3 scripts/validate.py` exits non-zero and names the template and the word

### Requirement: The user keeps, adapts or drops every rule
For each chosen template, the skill SHALL present every rule and ask whether the team would reject a change that broke it. For each rule the user SHALL choose keep, adapt or drop. Only kept and adapted rules SHALL be written to `standards/`. An adapted rule SHALL still have a reason and a check.

#### Scenario: Dropped rule
- **WHEN** the user drops `testing` rule §4 and keeps every other `testing` rule
- **THEN** the project's `standards/testing.md` does not contain the text of catalogue rule §4

#### Scenario: Adapted rule with no check
- **WHEN** the user rewords a rule so it no longer says what a reviewer can check
- **THEN** the skill asks for a checkable version before writing it

### Requirement: Existing practice is suggested, not decided
On a project with code, the skill SHALL preselect keep for rules the code already follows and show the evidence. The user SHALL still answer every rule.

#### Scenario: Code already follows a rule
- **WHEN** every migration in the project only adds columns or tables, and `persistence` has a rule that migrations are additive
- **THEN** the skill preselects keep for that rule, shows the migrations as evidence, and waits for the user's answer

### Requirement: Kept rules become numbered project standards
The skill SHALL write kept rules to `standards/<template>.md` (the architecture template to `standards/architecture.md`), numbered `§1` to `§n`, with every stack blank filled in from the user's answers or the project's code. On a re-run against an existing file, the skill SHALL append new rules with the next free number and SHALL NOT renumber existing rules.

#### Scenario: Blank filled in
- **WHEN** the user keeps a `persistence` rule containing `<migration tool>` and answers that the project uses a named migration tool
- **THEN** the rule in `standards/persistence.md` names that tool and contains no `<migration tool>` blank

#### Scenario: Re-run on an existing file
- **WHEN** `standards/testing.md` has §1 to §5, and a re-run adds two rules
- **THEN** the new rules are §6 and §7, and §1 to §5 are unchanged

### Requirement: Profile cites every kept rule after a confirmed diff
After writing `standards/`, the skill SHALL update `.claude/sdlc-profile.md` so that each kept rule is cited, as `standards/<file>.md §<n>`, in every profile section its catalogue entry names. It SHALL change only lines that cite a file under `standards/`. It SHALL match existing lines by the file and section they cite, so a reworded line is updated rather than duplicated. It SHALL show the full diff and write only after the user confirms. If the profile doesn't exist, the skill SHALL tell the user to run `init` and SHALL NOT create one.

#### Scenario: Rule cited in two sections
- **WHEN** the user keeps a rule whose profile sections are `implementation-rule` and `code-review`, written as `standards/architecture.md §1`
- **THEN** after confirmation the profile's Implementation rules and Code review checklist each contain a line citing `standards/architecture.md §1`

#### Scenario: User declines the diff
- **WHEN** the skill shows the profile diff and the user declines it
- **THEN** `.claude/sdlc-profile.md` is unchanged

#### Scenario: Other profile sections untouched
- **WHEN** the skill updates the profile
- **THEN** the Commands, Paths, Git, Task order and Formatting sections are byte-for-byte unchanged

#### Scenario: No profile
- **WHEN** the user runs `write-standards` in a project with no `.claude/sdlc-profile.md`
- **THEN** the skill tells the user to run `/sdlc-pipeline:init` and no profile exists afterwards

### Requirement: Init points to write-standards
When the profile's standards folder is missing, `init` SHALL suggest `/sdlc-pipeline:write-standards`. `init` SHALL NOT create the standards folder itself.

#### Scenario: Init on a project without standards
- **WHEN** the user runs `init` in a project with no `standards/` folder
- **THEN** `init`'s report suggests `/sdlc-pipeline:write-standards` and no `standards/` folder exists afterwards
