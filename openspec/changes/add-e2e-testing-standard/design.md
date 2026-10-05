## Context

The catalogue in `templates/standards/` holds two architecture templates and three concern
templates. `write-standards` lists every file under `concerns/`, so a new concern template appears
in the interview without a skill change. Every template is checked by `scripts/validate.py`:
rules numbered from §1, each with `Why`, `Check` and `Profile`, and no names from the stack list.
See proposal.md for motivation.

`concerns/testing.md` already covers testing at every level: a test per spec scenario, failure
paths, behaviour over implementation, independence and determinism. It says nothing about how
end-to-end tests are structured.

## Goals / Non-Goals

**Goals:**
- A team using the Screenplay pattern can adopt checkable e2e rules through `write-standards`.
- A team not using Screenplay can still keep the general e2e rules and drop the rest.
- The template names no tool, and the validator catches it if one slips in.

**Non-Goals:**
- Teaching the Screenplay pattern or any tool. Standards say what to do, not how a tool works
  (`docs/domain-and-standards.md`, "What to leave out").
- A Page Object alternative. It can be added later as alternative rules if a team asks for it.
- Changing `write-standards`, `init` or any agent.

## Decisions

### D1. A separate concern template, not more rules in `testing.md`

E2E testing goes in its own `concerns/e2e-testing.md`.

*Why:* not every project has a user interface, and `testing.md` rules apply to every project.
A separate template is picked or skipped as a whole. It also becomes its own
`standards/e2e-testing.md` in the project, so findings cite `standards/e2e-testing.md §<n>`.

*Alternative:* add the rules to `testing.md`. Rejected: projects without a UI would have to drop
each e2e rule one by one, and the file would grow past the six to eight rules a template should
have.

### D2. General e2e rules first, then Screenplay rules

The template has two kinds of rule. The general ones apply to any e2e suite:

- e2e tests cover use case main flows; alternative and exception flows are tested at lower levels;
- element locators are defined in one place and found by accessible role or test id, not page
  structure;
- each e2e test starts from its own known state.

The Screenplay rules follow:

- tests are written as an actor's goals, as Tasks named in glossary terms;
- Tasks are built from Interactions, and only Interactions touch the user interface;
- assertions go through Questions, not direct queries of the page;
- tools are reached only through Abilities.

That's seven rules. Each stands alone, so a team using page objects keeps the general rules and
drops the Screenplay ones. Rules don't refer to each other or to `testing.md` by number, because
the project's copy is renumbered after drops.

*Alternative:* a Screenplay-only template. Rejected: the general rules matter whatever the pattern,
and a team would otherwise get nothing from the template unless it used Screenplay.

### D3. The header defines the terms; it doesn't teach

The header comment gives one line each for Actor, Ability, Task, Interaction and Question, like
the ports-and-adapters definition in `hexagonal.md`. That's enough for the user to answer "would you
reject a change that broke this?" and for a reviewer to apply a rule. How to write Screenplay code
with a particular library belongs in the project's own docs or a project skill, which the project's
standard can cite once its blanks are filled in.

### D4. Blanks and profile targets

Blanks: `<e2e browser tool>`, `<screenplay library>`, `<e2e test location>` and
`<test id attribute>`. The interview fills them, for example with Playwright and Serenity/JS.

Profile targets follow the existing templates. Rules a plan can show (main flows only, tests named
by goal) target `plan-review`. Rules about test structure target `code-review`. The rule about
starting state also targets `verification`, because qa runs the suite.

### D5. Stack-name list additions

Add `playwright`, `serenity`, `cypress`, `selenium`, `webdriverio` and `puppeteer` to `STACK_NAMES`
in `scripts/validate.py`. "Serenity" and "selenium" are also ordinary words, but neither has a
reason to appear in a stack-agnostic template. The check is whole-word, so it doesn't match
inside longer words.

### Staying stack-agnostic and leaving OpenSpec alone

The template describes a pattern, not a library. Every tool name is a blank that only the
project's copy fills in. The validator's list now covers the e2e tools most likely to slip in.
Nothing touches OpenSpec artifacts or `openspec/config.yaml`.

## Risks / Trade-offs

- [Screenplay adds ceremony a small suite doesn't need] → Every Screenplay rule can be dropped on
  its own; the general rules still apply.
- [The "main flows only" rule conflicts with a team's habit of testing everything end to end] → It
  is a candidate like any other. If the team won't enforce it, they drop it.
- [Seven rules overlapping with `testing.md` add context cost] → The rules cover structure that
  `testing.md` doesn't; none of them repeats a `testing.md` rule.
- [A legitimate template one day needs the word "serenity"] → Unlikely; rename the word or remove it
  from the list then.

## Migration Plan

None. Existing projects are unaffected until they re-run `write-standards` and pick `e2e-testing`.
