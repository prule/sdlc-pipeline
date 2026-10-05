# API

<!--
Catalogue template for /sdlc-pipeline:write-standards. Not copied as is: the team keeps, adapts or
drops each rule, and the kept rules become the project's standards/api.md.

§1 and §2 are alternatives: keep at most one. A rule with an `Alternative to:` line excludes the
rule it names.

Rule format: `Why:` the reason, `Check:` what a reviewer looks for, `Profile:` the profile sections
that cite the rule (implementation-rule, plan-review, verification, code-review). <Angle brackets>
are stack blanks the interview fills in.
-->

## §1 The contract comes first
Why: consumers and providers agree the interface before anyone writes code against it.
Check: an API change edits <contract file> before or with the handler code, and handlers add no operation or field the contract doesn't declare.
Profile: implementation-rule, plan-review, code-review
Alternative to: §2

## §2 The contract is generated from the code
Why: the published contract can never drift from what the code does.
Check: an API change regenerates <contract file> with <generation command> in the same change, and nobody edits the generated file by hand.
Profile: implementation-rule, code-review
Alternative to: §1

## §3 Every error uses one format
Why: clients handle errors once, the same way, for every operation.
Check: every error response uses <error format> and carries a stable, machine-readable error code.
Profile: implementation-rule, code-review

## §4 Breaking changes need a new version
Why: existing clients keep working when the API changes.
Check: removing or renaming an operation or field, or making an optional input required, happens only in a new <version scheme> version.
Profile: plan-review, code-review

## §5 Input is validated at the edge
Why: the core can trust what it receives, and bad input gets a clear answer instead of a fault.
Check: every inbound field is validated before it reaches the use case, and invalid input returns the §3 error format, never a server fault.
Profile: implementation-rule, verification

## §6 Names come from the glossary
Why: the API speaks the business's language, so clients and the team mean the same thing.
Check: operation, resource and field names use terms from the domain glossary.
Profile: plan-review, code-review

## §7 Retried writes take effect once
Why: networks fail, and a retry must not create a second order or a second payment.
Check: every operation that creates or changes state can be retried safely, using <idempotency mechanism>, and a test sends the same request twice.
Profile: plan-review, verification
