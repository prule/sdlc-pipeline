# The pipeline

`/sdlc-pipeline:build-use-case <use case>` makes the main session the **orchestrator**. It does no
phase work itself. It spawns one agent per phase, passes the artifacts between them, enforces the
gates and keeps the run inside its budget.

```
architect ─▶ spec-reviewer ─▶ 🚦 GATE 1 ─▶ junior-dev ─▶ qa ─▶ senior-dev ─▶ 🚦 GATE 2 ─▶ archive ─▶ 📝 retro
  (plan)      (plan gate)      (you)        (implement)  (verify) (code review)  (you)
                   ▲                              │          │         │
                   └──── revise (max 2 rounds) ───┴──────────┴─────────┘
```

## Principle

**OpenSpec owns the workflow mechanics; agents own judgment and standards.** Each agent calls the
OpenSpec skill for its phase (`opsx:propose`, `opsx:apply`, `opsx:verify`) instead of re-implementing
it, and adds what OpenSpec can't know: the project's standards, domain language and stack rules,
which it reads from the profile, `CLAUDE.md`, `standards/` and `domain/`. See
[domain-and-standards.md](domain-and-standards.md) for what those two folders should hold.

## The team

| Agent | Can write? | Job | OpenSpec |
|-------|-----------|-----|----------|
| `use-case-writer` | use cases only | Rough idea → business use case (before the pipeline) | — |
| `architect` | planning artifacts | Use case → proposal, design, spec delta, tasks | `opsx:propose` |
| `spec-reviewer` | no (read-only) | Plan gate: standards conformance + design and task quality | — |
| `junior-dev` | yes | Implements the tasks | `opsx:apply` |
| `qa` | tests only | Every requirement has a useful test; runs the suite | `opsx:verify` |
| `senior-dev` | yes (fixes directly) | Final code review; fixes findings, hands back design and scope calls | — |

The `use-case-writer` agent drafts one use case in one shot and never edits `BACKLOG.md`. To write
the next backlog entry and record it there, use `/sdlc-pipeline:write-use-case next`.

All agents run on **opus**. On a measured run a cheaper implementer made about four times as many
tool calls and doubled the run's cost for the same review quality, so a cheaper model is a false
economy here. No agent can spawn agents; only the orchestrator does.

## Stages

0. **Prepare.** The orchestrator reads the profile and the use case, notes the use case's open
   questions, and makes sure it is on a use-case branch (`feat/uc-<n>-<slug>` from the base branch),
   never on the base branch itself.
1. **Plan.** The architect creates the OpenSpec change. Every main-flow step, alternative flow and
   business rule of the use case maps to a requirement or scenario, or is marked out of scope. The
   change must pass `openspec validate --strict`.
2. **Plan gate.** The spec-reviewer checks the plan against the profile's *Plan review* checklist,
   the domain docs, and design and task quality. On REQUEST CHANGES the architect revises.
   - 🚦 **Gate 1, you:** the proposal summary, the design decisions, the reviewer's verdict and every
     open question. You answer proceed, revise or stop.
3. **Implement.** The junior dev works `tasks.md` and verifies with the profile's Verify command.
   A blocker or plan defect goes back to the architect; the junior dev doesn't improvise.
4. **Verify.** QA builds a requirement → test checklist, adds missing tests, runs the suite and
   returns READY TO ARCHIVE or NOT READY. Defects go back to the junior dev.
5. **Code review.** The senior dev reviews the diff against the spec and the profile's *Code review*
   checklist, fixes what it finds and re-verifies. It hands back only what needs a design, plan or
   scope decision; that goes to the architect.
   - 🚦 **Gate 2, you:** the QA evidence, the review findings and the changed files. You approve the
     archive or not.
6. **Archive.** `openspec-archive-change` folds the spec delta into `openspec/specs/` and moves the
   change to `openspec/changes/archive/`. If the project has a `BACKLOG.md` (from
   `/sdlc-pipeline:plan-use-cases`), the orchestrator then ticks the use case's entry as built,
   updates the section's count and names the next entry. A run that stops before archive leaves
   `BACKLOG.md` unchanged.
7. **Retrospective, always.** See below.

## Budget guardrails

- **Fix loops** (spec-reviewer↔architect, qa↔junior-dev, senior-dev hand-backs) are capped at **2
  rounds**. A third attempt stops the run and escalates to you.
- **No progress twice in a row** from the same agent stops the run.
- **About 10 agent runs** without reaching Gate 2 pauses the run and asks whether to continue, narrow
  the scope or abort.
- **No silent scope growth:** work beyond the approved plan comes to you as a scope decision.
- **Fail closed:** when unsure whether to spend another round, the orchestrator asks.
- The only real dollar ceiling is your account's spend limit; set one. Watch spend with `/cost`.

## Retrospectives

Every run ends with `retrospectives/<YYYY-MM-DD>-<change>.md`, whether it was archived, stopped at a
gate, escalated or aborted. Failed runs teach the most. The orchestrator writes it from:

- the **Run-log findings** block that ends every spec-reviewer, qa and senior-dev report (one entry
  per finding, with a root cause and a recommended change to an input);
- your answer at each gate (a "revise" or "stop" is a failed review);
- every fix-loop round, stall and escalation;
- the session report it generates for the run.

Before writing, it reads the five most recent records and marks any finding that **recurs**. A
recurring finding means an input (a standard, the profile, an OpenSpec rule, an agent instruction,
the use-case template) isn't working, so its recommendation is ranked first. Recommendations always
change an input, never "be more careful".

Adopt a recommendation where its target lives: standards, the profile and domain docs are in the
project; agent and skill instructions are in this plugin, so open an issue or PR here.

## Running phases by hand

```
Use the sdlc-pipeline:architect agent to plan use-cases/UC-003-….md
Use the sdlc-pipeline:spec-reviewer agent to review the <change> change
Use the sdlc-pipeline:junior-dev agent to implement the <change> change
Use the sdlc-pipeline:qa agent to verify <change>
Use the sdlc-pipeline:senior-dev agent to review the diff for <change>
```

Or drive OpenSpec directly, with no agents:

```
/opsx:propose "<idea>"     # plan
/opsx:apply <change>       # implement
/opsx:verify <change>      # verify
/opsx:archive <change>     # fold the spec delta into openspec/specs and archive the change
```

OpenSpec cheat sheet: `openspec list`, `openspec show <change>`,
`openspec validate <change> --strict`, `openspec archive <change> --yes`. Plans live in
`openspec/changes/<name>/`; promoted specs in `openspec/specs/<capability>/spec.md`.

## Where rules come from

| Rule | Lives in | Read by |
|------|----------|---------|
| Roles, procedure, budget, output format | this plugin's `agents/` and `skills/` | every run |
| Stack facts: commands, paths, implementation rules, review checklists | project `.claude/sdlc-profile.md` | every agent |
| Design-time rules per artifact | project `openspec/config.yaml` | architect (via OpenSpec), spec-reviewer |
| Detailed standards | project `standards/` | cited by the profile; reviewers |
| Ubiquitous language, business rules | project `domain/` | use-case writer, architect, spec-reviewer |
| Always-on project instructions | project `CLAUDE.md` | every agent |

To change *how work is done* in one project, edit its standards or profile. To change *how the
pipeline works* everywhere, change this plugin.
