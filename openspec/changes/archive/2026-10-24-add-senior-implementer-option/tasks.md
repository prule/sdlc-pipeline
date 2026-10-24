# Tasks

## 1. Profile setting

- [x] 1.1 Add the `## Pipeline` section with `**Implementer:** junior-dev` to `templates/sdlc-profile.md` after `## Git`, worded as in design D1; verify the template still reads top to bottom with no leftover placeholder for this field.
- [x] 1.2 Document the `## Pipeline` section and the Implementer field (values, default when missing, the `--senior`/`--junior` override) in `docs/profile.md` under Sections; verify the field table names `build-use-case` as its reader.

## 2. Senior dev implement mode

- [x] 2.1 In `agents/senior-dev.md`, add `Skill` to `tools`, extend the description, and add the "Implement" section from design D5 ahead of "Code review"; verify the section points to `agents/junior-dev.md` instead of copying its procedure, and that "Fixing what you find" and "Verdict" still read as review-only.
- [x] 2.2 Check `agents/junior-dev.md` for wording that assumes it is the only implementer (description, "senior/architect input"); change only what is wrong, and verify no stage numbers or routing rules are restated there.

## 3. Orchestrator

- [x] 3.1 In `skills/build-use-case/SKILL.md`, update `argument-hint` and step 0 to strip a leading `--senior` or `--junior`, ask if both are given, and resolve the implementer as flag → profile → `junior-dev` with its source (design D2); verify a pasted use case that contains "--senior" mid-text is not treated as a flag.
- [x] 3.2 Add `Implementer: <agent> (<source>)` to what Gate 1 shows, and say that a Gate 1 answer naming the other agent switches it; verify against the "Human switches at Gate 1" scenario.
- [x] 3.3 Replace stage 3 with the wording in design D3 (resolved implementer, `Implement` description prefix, implementing-not-reviewing note for senior-dev), change stage 4 and the budget guardrail to "the implementer"; verify no remaining text sends QA defects to `junior-dev` by name.
- [x] 3.4 Add the stage 5 sentence from design D4 (fresh senior-dev run, never resume the implementer, pass only the change name, `Code review` description prefix); verify stage 5 still runs in both modes.
- [x] 3.5 In step 7, add `implementer` to the front-matter fields the orchestrator writes even when the project template lacks them; add `implementer: junior-dev | senior-dev` to `templates/retrospective.md` after `agent_runs`; verify against the run-retrospective scenarios.

## 4. Session report

- [x] 4.1 In `skills/session-report/session_report.py`, make `is_gate` take the run's description and return false for `senior-dev` runs whose description starts with `Implement` (case-insensitive); pass the description at the call site. Verify resumed runs still inherit the parent's flag.
- [x] 4.2 Make the per-agent table count `caught` and the catch-rate denominator over gate runs only, and mark the agent a gate if any of its runs is one (design D6).
- [x] 4.3 Add a `selftest.py` case: senior-dev "Implement UC-4", qa NOT READY with Q1, senior-dev resumed fix, qa re-verify, senior-dev "Code review UC-4" APPROVE. Assert one qa fix loop with the senior resume as fix run, no verdict on the implement run, `gate_runs` excluding it, and "caught 1/1"-style stats for senior-dev. Verify with `python3 skills/session-report/selftest.py`.
- [x] 4.4 Note the `Implement` description rule in `skills/session-report/README.md` where gate agents are explained; verify the README matches the code.

## 5. Docs, changelog and version

- [x] 5.1 Update `docs/pipeline.md`: the diagram caption or a note for the senior implementer, the team table (`senior-dev` also implements when chosen), stages 3–5, the fix-loop guardrail and "Running phases by hand"; verify every mention of who implements allows for both agents.
- [x] 5.2 Update `README.md`'s pipeline line or agent table with one sentence on the option; check `docs/evaluating-the-pipeline.md` for text that assumes junior-dev always implements and add a line on comparing runs by `implementer`.
- [x] 5.3 Add a `## [0.7.0]` entry to `CHANGELOG.md` (Added: Implementer setting, flags, senior-dev implement mode; Changed: build-use-case routing, retrospective field, session report gate rule; host projects need do nothing) and bump `version` to `0.7.0` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`; verify both manifests match.

## 6. Verification

- [ ] 6.1 Run `python3 scripts/validate.py` and `claude plugin validate .`; both pass.
- [ ] 6.2 In a host project, run `claude --plugin-dir <this repo>` and `/sdlc-pipeline:build-use-case --senior <use case>`. Check: Gate 1 shows `Implementer: senior-dev (flag)`; stage 3 spawns senior-dev with an `Implement` description and no junior-dev runs; any QA defect goes back to senior-dev; stage 5 is a new senior-dev run; the retrospective has `implementer: senior-dev`; the session report shows the implement run as a producer and any QA loop correctly.
- [ ] 6.3 In the same host project, run once with no flag and no `## Pipeline` section. Check the agents run in the old order (architect, spec-reviewer, junior-dev, qa, senior-dev) and the retrospective has `implementer: junior-dev`.
