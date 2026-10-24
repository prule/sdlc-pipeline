# Design

## Context

See proposal.md for why. Today `build-use-case` hard-codes `sdlc-pipeline:junior-dev` at stage 3
and sends QA defects to it at stage 4. `senior-dev` exists only as the stage 5 reviewer. Its
frontmatter tools are `Read, Write, Edit, Bash, Grep, Glob`, with no `Skill`, so it can't invoke
`opsx:apply` yet. Both agents already run on opus, so this switch changes the role and its
judgment, not the model.

`session_report.py` decides gate or builder from the agent type alone
(`GATE_AGENTS = {"spec-reviewer", "senior-dev", "qa", ...}`, `is_gate(subagent_type)`).
`build_fix_loops` treats every gate run as a loop boundary. So a senior-dev implement run would
get a keyword verdict, and a senior-dev fix after a QA rejection would end the loop as a "re-check"
by a different gate, with no fix runs. The loop would not be shown at all.

No retrospective or session report yet shows this failure. The change is a speed option the user
asked for, and the report fix stops the option breaking the report.

## Goals / Non-Goals

**Goals:**
- One switch, with a project default and a per-run override, that picks the stage 3 agent.
- An independent code review whichever agent implements.
- Retrospectives and session reports that stay correct and comparable across both modes.

**Non-Goals:**
- Skipping or merging any other stage (QA, code review, gates).
- Choosing the model or effort per agent. That stays in agent frontmatter and the user's settings.
- A new agent. The senior dev gains a mode; no `senior-implementer.md` is added.

## Decisions

### D1. The setting lives in a new `## Pipeline` profile section
The profile holds the facts the pipeline agents act on (docs/profile.md, "Profile, CLAUDE.md or
openspec/config.yaml?"), so the setting goes there. None of the existing sections fits: Commands,
Paths, Git and the rule sections describe the stack, and this setting describes the run. A
`## Pipeline` section also gives later run options a place to go.

Template addition, after `## Git`:

```markdown
## Pipeline

- **Implementer:** `junior-dev`. Who implements the approved plan: `junior-dev`, or `senior-dev`
  for a faster run with fewer fix rounds. Override one run with `--senior` or `--junior`.
```

A missing section means `junior-dev`, so existing profiles work without an edit. That is why the
plugin never has to write to the project-owned profile.

*Alternatives:* an env var or `settings.json` key. Plugins can't set either, and the profile is
already the file every agent reads. A flag-only switch: rejected, because the user wants a setting
that stays on.

### D2. The flags go before the use case and are stripped
`build-use-case` reads `$ARGUMENTS`. In step 0 the orchestrator removes a leading `--senior` or
`--junior` and treats the rest as the use case path or text. Resolution order: flag, then profile,
then `junior-dev`. It records the source (`flag` | `profile` | `default`) for Gate 1 and the
retrospective. The `argument-hint` becomes
`"[--senior | --junior] <use-cases/UC-n-slug.md, or the pasted use case>"`.

### D3. Stage 3 and stage 4 name "the implementer", not the junior dev
Current `skills/build-use-case/SKILL.md` stage 3:

> 3. **Junior dev (implement).** Spawn `sdlc-pipeline:junior-dev` on the approved change to work
> `tasks.md`. If it reports a blocker or a plan defect, route back to the architect (via the
> spec-reviewer if the plan itself is wrong) rather than letting it improvise.

Replacement:

> 3. **Implement.** Spawn the implementer resolved in step 0, `sdlc-pipeline:junior-dev` or
> `sdlc-pipeline:senior-dev`, on the approved change to work `tasks.md`. Give the Agent call a
> description that starts with `Implement` (e.g. `Implement UC-4`). When the implementer is
> `senior-dev`, tell it in the prompt that it is implementing, not reviewing. If it reports a
> blocker or a plan defect, route back to the architect (via the spec-reviewer if the plan itself
> is wrong) rather than letting it improvise.

Stage 4 changes "send defects to the junior dev" to "send defects to the implementer (resume the
same run with SendMessage where you can)". The budget guardrail line
"qa↔junior" becomes "qa↔implementer".

The `Implement` description prefix is the signal the session report keys on (D6). The orchestrator
already writes these descriptions, so this costs nothing.

### D4. Stage 5 spawns a fresh senior-dev
Current stage 5 opening: "Spawn `sdlc-pipeline:senior-dev` for a final code review of the diff."
Added sentence: "If the senior dev implemented the change, spawn a **new** senior-dev run; never
resume the implementing run, and pass only the change name, so the review does not inherit the
implementer's reasoning. Start its description with `Code review`."

This is the choice the user made: keep the independent review even though it costs a run. With a
fresh context the reviewer reads the diff against the spec cold, which is the point of the gate.
Gate 2 is unchanged.

Gate 1 adds one line to what it shows: `Implementer: <agent> (<source>)`. If the human's answer
names the other agent, the orchestrator uses it.

### D5. senior-dev gets an implement mode, not a copy of junior-dev
`agents/senior-dev.md` gains `Skill` in `tools` and a new section ahead of "Code review":

```markdown
## Implement (when the orchestrator asks you to implement)
Work the approved change exactly as `junior-dev` does: follow the Procedure, Rules, Budget
discipline and Output in `${CLAUDE_PLUGIN_ROOT}/agents/junior-dev.md`. Invoke `opsx:apply`, follow
the profile's Implementation rules, and paste the Verify output. You may use your judgment on
how to implement a task, but not on what the plan is: a blocker or plan defect is still reported,
not redesigned. Do not review your own work; a separate run does the code review.
```

The description gains: "Also implements the change when the project chooses the senior dev as
implementer." Pointing at `junior-dev.md` instead of copying it keeps one source for the implement
procedure, the same way agents point at `opsx:*` skills instead of restating them. The
"Fixing what you find" and "Verdict" sections stay review-only.

*Alternative:* a new `senior-implementer` agent. Rejected: a fifth copy of the implement rules to
keep in sync, and a new agent type to explain in the docs and reports.

### D6. The session report keys on description, not agent type
`is_gate` becomes `is_gate(subagent_type, description)`: `senior-dev` with a description starting
`Implement` (case-insensitive) is not a gate. Resumed runs inherit the parent's `gate` flag
already (line ~876), so a QA fix sent to the implementing run stays a builder run. The per-agent
stats count `caught` and runs over gate runs only, and set `gate` if any run was a gate.
`selftest.py` gets a case for D6's two spec scenarios. Python stays 3.8+, standard library only.

*Alternative:* an explicit marker in the prompt. The description is already parsed and shown in
the report, so it is the cheaper and more visible signal.

### D7. Retrospective field
`templates/retrospective.md` front matter gains `implementer: junior-dev | senior-dev` after
`agent_runs`. Step 7 of `build-use-case` says to add it even if the project's template lacks it,
as it already does for `agents`.

### Stack-agnostic and OpenSpec boundaries
Nothing names a language or tool: the setting chooses between two plugin agents. Both
implementers invoke `opsx:apply` for the apply mechanics, and nothing in this change restates
OpenSpec's procedure.

## Risks / Trade-offs

- [The senior dev implements and then a senior dev reviews, so both share blind spots] → The
  reviewer is a fresh run with only the change name, and QA still checks independently. The
  retrospective's `implementer` field lets teams compare catch rates between modes.
- [Saving less time than hoped, since stage 5 still runs] → The saving comes from fewer qa↔
  implementer loops and fewer in-place review fixes. The session report shows both, so a team can
  measure it.
- [Older session logs or hand-run phases with no `Implement` description] → They are counted as
  before (senior-dev = gate). Only `build-use-case` runs made after this change use the prefix.
- [A human types `--senior` mid-text by mistake] → Only a leading flag is parsed; anything else is
  part of the use case.

## Migration Plan

Nothing to migrate. Ship as 0.7.0. To roll back, set `**Implementer:** junior-dev` or remove the
section. A plugin downgrade ignores the section, because older versions never read it.
