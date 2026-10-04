# Hexagonal architecture (ports and adapters)

<!--
Catalogue template for /sdlc-pipeline:write-standards. Not copied as is: the team keeps, adapts or
drops each rule, and the kept rules become the project's standards/architecture.md.

The core (domain and use cases) defines ports: the interfaces it needs from the outside world and
the ones it offers. Adapters connect a port to something real: an inbound adapter turns a request
into a use case call; an outbound adapter implements a port with storage, messaging or another
system.

Rule format: `Why:` the reason, `Check:` what a reviewer looks for, `Profile:` the profile sections
that cite the rule (implementation-rule, plan-review, verification, code-review). <Angle brackets>
are stack blanks the interview fills in.
-->

## §1 The domain depends on nothing outside itself
Why: business rules stay testable and survive a change of framework or storage.
Check: no code in <domain location> refers to an adapter, a framework or an I/O library.
Profile: implementation-rule, plan-review, code-review

## §2 The core reaches the outside world only through ports
Why: the core can be run and tested without any real infrastructure.
Check: every call from <core location> to storage, messaging, time or another system goes through a port defined in the core.
Profile: implementation-rule, code-review

## §3 Adapters translate; they hold no business rules
Why: a rule hidden in an adapter is lost when the adapter is replaced.
Check: no adapter decides a business rule; it maps between the outside format and the port and nothing more.
Profile: code-review

## §4 Inbound adapters call use cases, not domain internals
Why: every way into the system goes through the same use case and the same checks.
Check: each inbound adapter calls a use case in the application layer, never a domain object's methods directly.
Profile: code-review

## §5 Ports are named for the domain, not the technology
Why: the port says what the core needs, so any adapter can meet it.
Check: no port's name or signature refers to a storage, transport or vendor technology; names use glossary terms.
Profile: plan-review, code-review

## §6 The plan names every port and adapter it adds or changes
Why: the reviewer can check the shape before any code exists.
Check: the design lists each new or changed port and the adapters that implement it.
Profile: plan-review

## §7 Use cases are tested with fake ports
Why: tests of business behaviour are fast and don't fail for infrastructure reasons.
Check: each use case has tests that use in-memory or fake port implementations and do no I/O.
Profile: verification

## §8 Each outbound adapter is tested against the real dependency
Why: fakes prove the core; only the real thing proves the adapter.
Check: each outbound adapter has a test against <the real dependency or a local instance of it>.
Profile: verification
