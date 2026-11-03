# Design

## Context

See proposal.md for why. QA's procedure today is: load the profile, `opsx:verify`, build the
requirement → test checklist, run **Verify**. Its verdict is READY TO ARCHIVE or NOT READY, and
`build-use-case` stage 4 sends NOT READY defects to the implementer, at most 2 rounds.

The host project in mind runs a SonarQube server and a `sonar-check` wrapper, which scans the repo,
waits for the quality gate and exits non-zero with the issue list when it fails. The plugin must not
depend on that tool: the hard constraint is that agents, skills and templates never assume a stack.

No retrospective or session report yet shows a static-analysis miss. The change is an option the
user asked for.

## Goals / Non-Goals

**Goals:**
- One profile switch, off by default, that adds a static-analysis scan to QA.
- Scan findings flow through the existing fix loop, with no new loop or stage.
- The human sees at Gate 2 whether the scan ran and what it said.

**Non-Goals:**
- A per-run flag. The user asked for a setting; a flag can come later if runs need it.
- Running the scan in any other agent. Projects that want every agent to run it already can, by
  adding it to **Verify**.
- Setting up the analysis server, its token or its quality-gate rules. Those are the project's.
- New finding kinds or session-report changes. Scan findings use the existing kinds.

## Decisions

### D1. The setting is a command, not on/off
The field holds `off` or the command to run:

```markdown
- **Static analysis:** `off`. A scan QA runs after Verify, or `off`. To turn it on, give the
  command that scans the project and exits non-zero when the quality gate fails, e.g. `sonar-check`.
```

A command keeps the plugin stack-agnostic: QA runs whatever the profile names, the same way it runs
**Verify**, and no agent or skill names a tool. An `on`/`off` switch would have to hard-code a
command. A missing field means `off`, so existing profiles need no edit and the plugin never writes
to the project-owned profile.

It goes in `## Pipeline`, not `## Commands`, because it says whether a pipeline step runs. Commands
holds the ones every agent uses.

*Alternative:* append the scan to **Verify**. Rejected as the mechanism (every agent runs it, every
time), but it stays open to projects that want that.

### D2. QA runs it once, after Verify passes
Current `agents/qa.md` procedure step 4:

> 4. Run the full build and test suite with the profile's **Verify** command, capturing the real
> output. Confirm every task in `tasks.md` is actually done in the code, not just checked off.

New step 5:

> 5. **Static analysis.** If the profile's **Pipeline → Static analysis** names a command, run it
> once, after **Verify** passes, and paste its output. If the field is missing or `off`, skip this
> step. If **Verify** failed, skip it too and say so: the scan is not worth running on code that
> does not build.

Scanning only green code avoids a second set of findings on code that will change anyway, and keeps
one scan per QA round.

### D3. Findings are defects; a scan that can't run is infra
New rules in `agents/qa.md`:

> - **Static-analysis findings are defects.** When the scan fails its quality gate, each issue it
>   lists is a defect: kind `code-defect`, or `standards-violation` when a profile rule covers it,
>   with the analyser's rule key in `rule`. Hand them back; don't fix production code. An issue the
>   change silences with a suppression comment, without a reason next to it, is a defect too.
> - A scan that cannot run (server unreachable, no token, the command missing) is an infra issue,
>   not a defect. Report it once, set the result to `not run (<reason>)` and judge the verdict on
>   the rest of the evidence. Don't retry it.

The infra rule matches QA's existing rule for environmental test failures. Making it block the
verdict would send the implementer a defect it can't fix. The human still sees `not run` at Gate 2
and can stop there.

### D4. A one-line result in QA's report and at Gate 2
QA's **Output** gains: `Static analysis: off | passed | failed (<n> issues) | not run (<reason>)`.
`build-use-case` Gate 2 currently shows "QA verdict + evidence, the code-review findings, and the
list of files changed"; it adds "and QA's **Static analysis** line". The orchestrator relays the
line; it does not run the scan.

### Stack-agnostic and OpenSpec
No agent, skill or template names a tool except as a profile example (`e.g. sonar-check`), the same
way **Verify** shows `e.g. npm test`. OpenSpec's verify mechanics are untouched: the scan is an
extra piece of evidence QA collects after `opsx:verify`.

## Risks / Trade-offs

- **A scan adds a minute or more to each QA round.** Off by default; the project chooses.
- **Findings outside the change.** A quality gate on new code reports only what the change touched.
  A gate that judges the whole project can fail on old code; QA reports what the command says, and
  the profile's command is the place to scope it.
