## Context

`skills/session-report/session_report.py` (about 1,700 lines, standard library only) reads a session
transcript and the subagent transcripts beside it, and writes one self-contained HTML report.
`build-use-case` runs it with `--compact --summary` at the end of every run and copies `session`,
`report`, `claude_code`, `orchestrator` and `agents` from the printed JSON into the retrospective.

What the logbook UC-0.1 run (`47d3f4bc…`, 5 subagent transcripts, 11 agent runs) showed about the
current code:

- `link_subagents()` matches transcripts to Agent calls by the first 120 characters of the prompt.
  Every transcript also has `agent-<id>.meta.json` with `toolUseId`, `agentType`, `description` and
  `spawnDepth`.
- A resumed agent (`SendMessage`) appends to its first transcript. `link_subagents()` sets
  `sub = None` on resumed runs, so all inner work lands on the first run. The architect transcript
  spans 41 minutes across four runs.
- `context_signals()` and `file_ops_from_tools()` only see `Read`, `Write` and `Edit`. Inside the
  subagents, `cat` ran 21 times, `grep` 7 and `sed` 6.
- `classify_review()` guesses verdicts from keywords and `truncate()` takes a slice of the answer.
  The agents already end with a structured **Run-log findings** block (`agents/qa.md`,
  `agents/spec-reviewer.md`, `agents/senior-dev.md`).

See proposal.md for motivation and specs/session-report/spec.md for the required behaviour.

## Goals / Non-Goals

**Goals:**
- Every number in the report is either right or labelled with how it was estimated.
- Each agent run, including resumed runs, carries its own cost.
- The summary file holds everything a later trends report needs, so old transcripts never have to
  be re-parsed.
- Older transcripts still produce a report.

**Non-Goals:**
- The trends report across runs. This change only makes its input possible.
- Prices or dollar cost.
- Agents started by other agents (`spawnDepth` above 1). They are linked and counted, but get no
  special layout.
- New `--compare` metrics. Compare mode reuses the analysis, so it picks up the corrected counts and
  nothing else.
- Changing what the agents write or what the retrospective records.

## Decisions

### D1. Link by `toolUseId`, fall back to the prompt

`load_subagents()` reads `agent-<id>.meta.json` when present and keys the transcript by its
`toolUseId`. `link_subagents()` links each Agent call by its tool-use id first, then by prompt for
transcripts with no meta file. It records how many runs used each method, and the report shows a
note when any run was linked by prompt.

*Why:* the id is exact. Prompt matching fails silently when two runs open with the same text, such as
repeated "Review the change …" prompts.

*Alternative:* match on `description` from the meta file. Rejected: descriptions repeat too.

### D2. Split transcripts by the parent's run start times

The main transcript already gives each run's start time, resumed runs included (the `SendMessage`
call). For an agent with several runs, each event in its transcript belongs to the latest run that
started at or before the event's timestamp. Tool calls, tokens, files and duration are then
computed per segment.

The "The coordinator sent a message while you were working" user message in the subagent
transcript is used only as a cross-check. If the number of markers doesn't match the number of
resumes, the report keeps the split but notes the mismatch. If the parent has no start time for a
resume, that agent falls back to today's behaviour and the report says so.

*Why:* timestamps come from the parent transcript, which the script already parses reliably. The
marker text is undocumented and could change in any Claude Code release.

*Alternative:* split on the marker text alone. Rejected for that reason.

### D3. Shell commands: common forms only, labelled

A small parser looks at each Bash command. It splits on `&&`, `||`, `;` and `|`, tokenises each part
with `shlex`, and recognises:

- reads: `cat`, `head`, `tail`, `less`, `wc`, `sed -n`, `grep`, `rg` (file arguments only);
- writes: `>` and `>>` targets, `tee`, `sed -i`, `cp` and `mv` destinations.

Paths are resolved against the transcript's `cwd`, ignoring `cd` within the command. Anything the
parser can't tokenise is skipped. Counts that include shell access are labelled "incl. shell".

The files panel drops paths under the session's own folder (`tool-results/`, `subagents/`), the
scratchpad and `~/.claude/`, and shows the rest relative to the project root (the transcript's
`cwd`). Paths outside the project are shown in full.

*Why:* the common forms cover what the agents actually did in the logbook run. A full shell parser
isn't possible with the standard library, and a wrong count labelled as an estimate does less harm
than a missing one.

### D4. Parse the Run-log findings block

For each gate run's result (the hand-back text when there is one), find the `## Run-log findings`
heading and read each `- **<ID>** · key: value · key: value …` entry, including continuation lines
up to the next entry. Keys read: `kind`, `severity`, `rule`, `where`, `status`, plus the `root
cause` and `recommendation` sub-bullets. The id is any capital letters followed by digits, so new
gates work unchanged. `None` means a gate ran and found nothing.

A gate run's verdict comes from its findings when it has a block: it handed something back if any
finding's status is `handed-back`, and fixed something if any is `fixed-in-place`. Without a block,
`classify_review()` runs as today and the verdict is marked "inferred". The snippet shown is the
verdict line or the first finding, not a slice from the middle of the text.

### D5. Fix loops from the run sequence

Fix loops come from walking the runs in start order. A loop starts at a gate run that handed findings
back (or, with no block, had an inferred rejecting verdict). The non-gate runs that follow are the
fix runs, as long as each is a resumed run or an agent type that already ran before the gate. A
fresh agent of a new type (such as the first junior-dev after the plan gate) starts the next phase
and ends the loop. The next run of the same gate type is the re-check, and the loop ends there; a
run of a different gate ends it without a re-check, shown as "not re-checked". A rejection with no
fix run is not a loop; its findings still show as handed back. A loop's cost is the sum of its fix
and re-check runs' time, tool calls and tokens.

The phase rule came from the logbook UC-0.1 run: without it, the plan re-review's two advisory
findings pulled the whole implementation run into a "fix loop".

### D6. Time breakdown

- **Agents:** the union of all agent run intervals, so parallel runs count once.
- **Waiting on the human:** `AskUserQuestion` durations, plus the gap from the orchestrator's last
  event to the next real user prompt, counting only the parts not already covered by an agent run.
- **Orchestrator:** wall time minus the other two.

With `--compact`, idle gaps are collapsed in the timeline only. The breakdown always uses real time.

### D7. Summary file

The summary is written to `<out-dir>/<session>.summary.json` on every run, and `--summary` prints the
same object. The existing fields keep their names and meaning, so `build-use-case` and the
`run-retrospective` spec are unaffected. New fields:

```json
{
  "schema": 1,
  "summary": "reports/sessions/<session>.summary.json",
  "use_case": "UC-0.1", "change": "uc-0-1-open-logbook",
  "time":   {"wall_s": 2534, "agents_s": 1650, "human_wait_s": 304, "orchestrator_s": 580},
  "tokens": {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0},
  "agents": {"qa": {"model": "...", "effort": "...", "runs": 2,
                    "duration_s": 486, "tool_calls": 33, "tokens": {"...": 0}}},
  "runs": [{"id": "toolu_…", "agent": "qa", "description": "Verify UC-0.1",
            "start": "2026-10-05T02:01:45Z", "duration_s": 433, "resumed": false,
            "linked_by": "id", "tool_calls": 21, "tokens": {"...": 0},
            "verdict": "handed-back", "verdict_source": "findings", "findings": ["Q1", "Q2"]}],
  "findings": [{"id": "Q1", "gate": "qa", "run": "toolu_…", "kind": "test-gap",
                "severity": "high", "rule": "standards/testing.md §2", "where": "src/a.ts:10",
                "status": "handed-back", "root_cause": "...", "recommendation": "..."}],
  "fix_loops": [{"gate": "qa", "started_by": "toolu_…", "findings": ["Q1", "Q2", "Q3"],
                 "fix_runs": ["toolu_…"], "recheck_run": "toolu_…",
                 "duration_s": 256, "tool_calls": 15, "tokens": {"...": 0}}]
}
```

`schema` starts at 1 and goes up whenever a field changes meaning, so a trends report can tell
versions apart. `agents` keeps its existing three fields and gains the new ones.

### D8. Layout

The new order follows the spec. Specifics:

- **Header:** the use case id and change name when found, otherwise the session title. The use case
  comes from a `use-cases/UC-….md` path in the `build-use-case` arguments. The change is the name
  passed to `openspec … --change` most often, or the name in `openspec new change`.
- **Cards:** wall time with its breakdown, agent runs, fix loops, findings by severity, total
  tokens.
- **Timeline:** one lane per agent type. Each run is a bar, and resumed runs sit on the same lane.
  A "you" lane shows the human waits. Fix loops are drawn as brackets from the gate run to the
  re-check.
- **Findings, agents, context:** open by default.
- **Errors, tool usage, files, activity feed:** inside `<details>` elements, closed by default.

The report stays a single self-contained HTML file with inline CSS and the small inline script it
already has. It loads nothing from the network, and keeps the existing light and dark themes.

### D9. A synthetic transcript to check the parsing

Add `skills/session-report/selftest.py` and a small fixture folder of hand-written transcripts:

- one with a resumed agent and meta files;
- one without meta files;
- one with a findings block, shell reads and a gate wait.

The self-test runs the analysis on each fixture and asserts the numbers in the spec scenarios.
`scripts/validate.py` runs it, so CI catches regressions.

*Why:* the parsing rules in D2 to D6 have many edge cases, and the repo's usual check (a manual run in
a host project) only covers whatever that one run happened to contain.

*Alternative:* check only by hand against the logbook and sdlc transcripts. Rejected as the only
check: transcripts get deleted, and they can't be committed (they hold project content). Those manual
runs still happen as a final check.

### Staying stack-agnostic and leaving OpenSpec alone

The report reads Claude Code transcripts and the agents' own findings format. It names no language
or framework. The shell parser recognises Unix file commands, not project tools. It reads OpenSpec
only as text in commands, to find the change name, and never calls OpenSpec.

## Risks / Trade-offs

- [Claude Code changes the meta file or transcript format] → Every new source has a fallback (D1, D2)
  and the report says when one was used. The self-test fixtures record the current format.
- [The shell parser over- or under-counts] → It covers common forms only, and the counts are labelled
  "incl. shell". A wrong context count is less misleading than "never read" next to six catches.
- [A gate writes a malformed findings block] → Entries that don't parse are skipped, and the run
  falls back to the inferred verdict, marked as such.
- [Fix-loop boundaries are wrong when the orchestrator interleaves gates] → Loops are matched by gate
  type, and a loop without a re-check is shown as such rather than guessed.
- [The script grows past 2,000 lines] → Keep it as one file so `build-use-case` and the skill still
  call one script, but group the new code into clearly marked sections. Splitting it into modules
  can be a later change.

## Migration Plan

None for host projects. New reports gain a `.summary.json`. Old reports stay as they are; re-running
the script on a transcript that still exists regenerates both files. Rollback is reverting the
release.

### D10. `build-use-case` names the summary file in its commit reminder

`build-use-case` doesn't commit reports itself; it reminds the human. Its current wording (step 6):

> Remind the human to commit the retrospective and session report with the change, and to open the
> PR against the profile's PR target.

Replacement:

> Remind the human to commit the retrospective, the session report and its `.summary.json` with the
> change, and to open the PR against the profile's PR target.

There's no recorded failure; without this, the summary file is easy to leave out of the commit, and
the trends report would have gaps.
