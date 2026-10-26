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

The implementer is `junior-dev` unless the profile's **Pipeline → Implementer** says `senior-dev`,
or the run passes `--senior` (`--junior` forces the junior dev). See
[Choosing the implementer](#choosing-the-implementer).

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
| `junior-dev` | yes | Implements the tasks (the default implementer) | `opsx:apply` |
| `qa` | tests only | Every requirement has a useful test; runs the suite | `opsx:verify` |
| `senior-dev` | yes (fixes directly) | Final code review; fixes findings, hands back design and scope calls. Implements the tasks when chosen as implementer | `opsx:apply` (when implementing) |

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
3. **Implement.** The implementer (the junior dev, or the senior dev if chosen) works `tasks.md`
   and verifies with the profile's Verify command. A blocker or plan defect goes back to the
   architect; the implementer doesn't improvise.
4. **Verify.** QA builds a requirement → test checklist, adds missing tests, runs the suite and
   returns READY TO ARCHIVE or NOT READY. Defects go back to the implementer.
5. **Code review.** The senior dev reviews the diff against the spec and the profile's *Code review*
   checklist, fixes what it finds and re-verifies. It hands back only what needs a design, plan or
   scope decision; that goes to the architect. If the senior dev implemented, this is a new
   senior-dev run that sees only the change name, so the review stays independent.
   - 🚦 **Gate 2, you:** the QA evidence, the review findings and the changed files. You approve the
     archive or not.
6. **Archive.** `openspec-archive-change` folds the spec delta into `openspec/specs/` and moves the
   change to `openspec/changes/archive/`. If the project has a `BACKLOG.md` (from
   `/sdlc-pipeline:plan-use-cases`), the orchestrator then ticks the use case's entry as built,
   updates the section's count and names the next entry. A run that stops before archive leaves
   `BACKLOG.md` unchanged.
7. **Retrospective, always.** See below.

## Choosing the implementer

| Setting | Who implements |
|---------|----------------|
| No `## Pipeline` section, or `**Implementer:** junior-dev` | `junior-dev` |
| `**Implementer:** senior-dev` in the profile | `senior-dev` |
| `--senior` before the use case | `senior-dev`, this run only |
| `--junior` before the use case | `junior-dev`, this run only |

Gate 1 shows the choice and where it came from (`Implementer: senior-dev (flag)`). Name the other
agent in your answer to switch. The senior dev implements to the same rules as the junior dev: it
follows the plan and reports plan defects instead of redesigning. QA defects go back to it. The
code review is still a separate senior-dev run. You save the junior dev's fix rounds, not the
review. Each retrospective records `implementer`, so you can compare the two modes.

## Budget guardrails

- **Fix loops** (spec-reviewer↔architect, qa↔implementer, senior-dev hand-backs) are capped at **2
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

Recommendations always change an input (a standard, the profile, an OpenSpec rule, an agent
instruction, the use-case template), never "be more careful".

### The recommendation ledger

`retrospectives/LEDGER.md` keeps one line per open or recurring recommendation: an id (`L-<n>`),
the recommendation, its target, the number of records it appears in, and a status. It makes
lessons get adopted instead of just recurring:

1. **Step 0.** The orchestrator reads the open lines and briefs the architect on each one that
   applies to the use case. Later agents get the lines for their phase.
2. **Gate 1.** The orchestrator lists the applying lines that are **due** (3 or more records). For
   each, you adopt it in this run, or give a reason to keep it open or to close it.
3. **Step 7.** The orchestrator matches each new recommendation to an open line. A match adds 1 to
   the line's count, ranks the recommendation first, and puts `· ledger: L-<n>` in the record. A new
   recommendation that is still open after the run gets a new line. Lines adopted or closed at
   Gate 1 move to *Closed*.

If the ledger is missing, step 7 creates it from [`templates/ledger.md`](../templates/ledger.md) and
seeds it with the recommendations that recur in the five most recent records. After that, the
ledger's counts replace reading earlier records for recurrence. Commit `LEDGER.md` with the
retrospective.

Adopt a recommendation where its target lives: standards, the profile and domain docs are in the
project; agent and skill instructions are in this plugin, so open an issue or PR here. Put the PR
or issue in the ledger line's status.

## Running phases by hand

```
Use the sdlc-pipeline:architect agent to plan use-cases/UC-003-….md
Use the sdlc-pipeline:spec-reviewer agent to review the <change> change
Use the sdlc-pipeline:junior-dev agent to implement the <change> change
Use the sdlc-pipeline:senior-dev agent to implement the <change> change   # instead of junior-dev
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
