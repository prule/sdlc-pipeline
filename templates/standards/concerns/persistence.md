# Persistence

<!--
Catalogue template for /sdlc-pipeline:write-standards. Not copied as is: the team keeps, adapts or
drops each rule, and the kept rules become the project's standards/persistence.md.

Rule format: `Why:` the reason, `Check:` what a reviewer looks for, `Profile:` the profile sections
that cite the rule (implementation-rule, plan-review, verification, code-review). <Angle brackets>
are stack blanks the interview fills in.
-->

## §1 Every schema change is a migration
Why: every environment reaches the same schema the same way, and the history is in version control.
Check: each schema change is a new migration in <migration location>, run by <migration tool>; nothing changes the schema by hand.
Profile: implementation-rule, code-review

## §2 Applied migrations are never edited
Why: an environment that already ran a migration never sees the edit, so environments drift apart.
Check: the diff changes no migration that already exists on <base branch>.
Profile: code-review

## §3 Migrations are additive
Why: during a deploy the old and new code run against the same schema, so neither may break.
Check: a migration doesn't drop or rename a table or column, or make an existing column required, in the same release as the code that stops using it.
Profile: implementation-rule, plan-review, code-review

## §4 Destructive changes take two releases
Why: the old code is gone before its data is.
Check: a drop or rename is planned as two changes: first add the new shape and use it, then remove the old shape in a later change.
Profile: plan-review

## §5 Queries live only in the data access code
Why: storage can change without hunting for queries across the codebase.
Check: queries and storage calls appear only in <data access location>.
Profile: code-review

## §6 Uniqueness and required relationships are also enforced by the store
Why: code-level checks race; a constraint in the store doesn't.
Check: every business rule about uniqueness or a required relationship has a matching constraint in a migration.
Profile: plan-review, code-review

## §7 Queries on large tables are indexed
Why: a query that's fast in a test can be slow on production data.
Check: every new filter or sort on <large tables> is covered by an index added in a migration.
Profile: code-review
