# Layered architecture

<!--
Catalogue template for /sdlc-pipeline:write-standards. Not copied as is: the team keeps, adapts or
drops each rule, and the kept rules become the project's standards/architecture.md.

Layers, top to bottom: presentation (handles requests), application (runs use cases), domain
(business rules), data access (storage and other systems).

Rule format: `Why:` the reason, `Check:` what a reviewer looks for, `Profile:` the profile sections
that cite the rule (implementation-rule, plan-review, verification, code-review). <Angle brackets>
are stack blanks the interview fills in.
-->

## §1 Each layer depends only on the layers below it
Why: a change to how requests arrive or data is stored doesn't ripple up into the business rules.
Check: no code in a lower layer refers to code in a higher one, using the layer locations <presentation, application, domain, data access locations>.
Profile: implementation-rule, plan-review, code-review

## §2 Business rules live in the domain layer
Why: each rule is decided in one place, so it can be found, tested and changed once.
Check: no presentation or data access code decides a business rule; it calls the application or domain layer instead.
Profile: implementation-rule, code-review

## §3 Presentation reaches data only through the application layer
Why: every request goes through the same use case, with the same checks.
Check: no code in <presentation location> calls data access code directly.
Profile: code-review

## §4 Every new component belongs to one named layer
Why: a reviewer can see where code went and whether the dependency direction holds.
Check: the plan names the layer of each new component, and each new file is in that layer's location.
Profile: plan-review, code-review

## §5 Storage types don't leak above the application layer
Why: the presentation layer stays independent of how data is stored.
Check: no type from <data access location> appears in a presentation-layer signature or response.
Profile: code-review

## §6 The application layer owns transactions
Why: one use case is all-or-nothing, wherever its data ends up.
Check: transactions start and end in application layer code, not in presentation or data access code.
Profile: implementation-rule, code-review

## §7 Domain rules are tested without the other layers
Why: tests for business rules stay fast and fail only when a rule is wrong.
Check: each business rule has a test that runs without presentation or data access code.
Profile: verification
