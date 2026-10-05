# End-to-end testing

<!--
Catalogue template for /sdlc-pipeline:write-standards. Not copied as is: the team keeps, adapts or
drops each rule, and the kept rules become the project's standards/e2e-testing.md.

§1 to §3 apply to any end-to-end suite. §4 to §7 apply the Screenplay pattern; a team that doesn't
use it drops them. Screenplay terms:
- Actor: a person or system using the application, named for a persona in the domain docs.
- Ability: what lets an actor use a tool, such as a browser or an API client.
- Task: a step towards the actor's goal, in business terms, made of other Tasks or Interactions.
- Interaction: one low-level action on the system, such as a click, a typed value or a request.
- Question: what an actor asks of the system's state, used to make assertions.

Rule format: `Why:` the reason, `Check:` what a reviewer looks for, `Profile:` the profile sections
that cite the rule (implementation-rule, plan-review, verification, code-review). <Angle brackets>
are stack blanks the interview fills in.
-->

## §1 End-to-end tests cover use case main flows
Why: end-to-end tests are slow and brittle, so they prove the journeys that matter and leave the edge cases to faster tests.
Check: each test in <e2e test location> follows a use case's main flow; alternative and exception flows are tested at a lower level, not end to end.
Profile: plan-review, code-review

## §2 Element locators live in one place and use roles or test ids
Why: a changed page breaks one locator, not every test, and tests don't depend on layout.
Check: tests find elements by accessible role and name, or by <test id attribute>, defined once per page or component; no test uses CSS structure or position.
Profile: implementation-rule, code-review

## §3 Each test starts from its own known state
Why: a test that depends on data left by another fails for reasons unrelated to the code.
Check: each test sets up the data it needs before it starts and passes when run alone or in any order.
Profile: verification, code-review

## §4 Tests are written as the actor's goals
Why: a test that reads like the use case shows what broke in business terms, and survives a redesign of the screens.
Check: each test reads as an actor performing Tasks named in glossary terms; clicks, typing and selectors don't appear in the test body.
Profile: plan-review, code-review

## §5 Only Interactions touch the user interface
Why: changes to the UI are fixed in the Interactions, and the Tasks above them stay stable.
Check: Tasks are built from other Tasks and Interactions; no Task calls <e2e browser tool> directly.
Profile: implementation-rule, code-review

## §6 Assertions go through Questions
Why: the same check reads the same way in every test, and can be reused.
Check: every assertion asks a Question; no test queries the page or the browser directly to assert.
Profile: code-review

## §7 Actors reach tools only through Abilities
Why: the tool can be configured or replaced in one place, and an actor's capabilities are explicit.
Check: <e2e browser tool> and API clients are given to actors as Abilities through <screenplay library>; no Task or Question creates its own.
Profile: code-review
