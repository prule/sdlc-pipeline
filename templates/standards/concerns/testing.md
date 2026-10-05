# Testing

<!--
Catalogue template for /sdlc-pipeline:write-standards. Not copied as is: the team keeps, adapts or
drops each rule, and the kept rules become the project's standards/testing.md.

Rule format: `Why:` the reason, `Check:` what a reviewer looks for, `Profile:` the profile sections
that cite the rule (implementation-rule, plan-review, verification, code-review). <Angle brackets>
are stack blanks the interview fills in.
-->

## §1 Every spec scenario has a named test
Why: the spec is the contract; a scenario without a test is a promise nobody checks.
Check: tasks.md names the test for each scenario in the change's spec delta, and that test exists and exercises the scenario's input.
Profile: plan-review, verification

## §2 Failure paths are tested
Why: most defects live in the alternative and exception flows, not the main flow.
Check: every alternative or exception flow, and every error a requirement names, has a test that triggers it.
Profile: verification

## §3 Tests check behaviour, not implementation
Why: a test tied to internals breaks on every refactor and misses real regressions.
Check: assertions are on outputs, stored state or observable effects; no test only asserts which internal method was called.
Profile: code-review

## §4 Test doubles replace only what the project doesn't own
Why: faking your own code hides the bugs between its parts.
Check: doubles stand in only for <external services>, time and randomness; collaborators inside the project are real.
Profile: code-review

## §5 Persistence is tested on the production engine
Why: an in-memory substitute behaves differently on exactly the queries that matter.
Check: tests of data access run against <production database engine> or a local instance of it.
Profile: implementation-rule, verification

## §6 Tests are independent
Why: a test that needs another test to run first fails for reasons unrelated to the code.
Check: each test sets up its own data and passes when run alone or in any order.
Profile: code-review

## §7 Tests are deterministic
Why: a flaky test teaches the team to ignore failures.
Check: no test depends on the real clock, the network or unseeded random values.
Profile: code-review

## §8 Test names state the condition and the outcome
Why: a failing test's name should say what broke without reading its body.
Check: each test name says the situation and the expected result.
Profile: code-review
