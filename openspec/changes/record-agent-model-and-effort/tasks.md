## 1. Session report: extract model, effort and version

- [x] 1.1 In `skills/session-report/session_report.py`, add an effort extractor next to `primary_model`. Per assistant message it takes `perTurnEffort`, then `effort`; an agent's value is the sorted, comma-joined set of values, or `unknown` if there are none. Store it on each subagent record (`load_subagents`). Verify by running the script on a recent session with subagents and printing the extracted values: opus-5-5 runs show `medium`, and the haiku `claude-code-guide` run shows `unknown`.
- [x] 1.2 In `link_subagents`, carry `effort` onto each agent run the same way `model` is carried, including resumed runs inheriting from their parent. Missing values become `unknown`, not `None`. Verify on a session with a resumed agent that the resumed run shows its parent's effort.
- [x] 1.3 In `analyze`, collect the set of every `version` seen (not just the first) and the main session's model and effort, using the same rules as 1.1. Verify that a session's header still shows `v2.1.288`, and shows a list if the transcript has more than one version.

## 2. Session report: HTML and summary output

- [x] 2.1 In `render_value_table`, add an **Effort** column after **Model**, aggregated per agent type like models. Verify that the generated report's table has the column, with `unknown` where nothing was recorded.
- [x] 2.2 Add a `--summary` flag. When set, after writing the HTML, print exactly one JSON object (shape in design.md, Decision 3) with full model IDs, and suppress the status lines. Verify with `python3 skills/session-report/session_report.py <log> --compact --summary | python3 -m json.tool` on a pipeline session: it parses, `runs` matches the report's Runs column, and `report` points at a file that exists.
- [x] 2.3 Verify the edge cases: a session with no subagents gives `"agents": {}` with `orchestrator` filled in, and running without `--summary` prints the usual two lines and no JSON.
- [x] 2.4 Update the module docstring usage line and the `--summary` help text. Confirm with `--help`.

## 3. Retrospective and orchestrator

- [x] 3.1 In `templates/retrospective.md`, add `claude_code`, `orchestrator` and `agents` to the front matter after `agent_runs`, using the flow-map format from design.md (Decision 4) with placeholder values. Verify the front matter still parses as YAML (`python3 -c` with a minimal parse, or by eye if no YAML parser in the stdlib).
- [x] 3.2 In `skills/build-use-case/SKILL.md` step 7, replace the *Session report* bullet with the replacement wording in design.md (Decision 5). Verify the diff touches only that bullet.
- [x] 3.3 In `templates/retrospectives-README.md`, mention that the front matter records the model and effort each agent ran, as recorded by Claude Code. Verify by reading the rendered file.

## 4. Docs, changelog and version

- [x] 4.1 `docs/observability.md`: in the Session report section, say the report shows model, effort and Claude Code version per agent, and that `--summary` feeds the retrospective. Add the effort caveat (undocumented fields, `unknown` when absent, may reflect the session setting).
- [x] 4.2 `docs/evaluating-the-pipeline.md`: add effort to the "Model (per agent)" row and to the "agent on an unexpected model" checklist item. Note that retrospectives can be grepped across runs for model and effort.
- [x] 4.3 `skills/session-report/README.md` and `skills/session-report/SKILL.md`: document the Effort column and the `--summary` option and its JSON shape.
- [x] 4.4 `CHANGELOG.md`: add a `0.2.0` entry under **Added** covering the report columns, `--summary`, and the retrospective fields. Note that host projects need do nothing.
- [x] 4.5 Bump `version` to `0.2.0` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Verify they match.

## 5. Validation

- [x] 5.1 Run `python3 scripts/validate.py` and `claude plugin validate .`, and verify both pass.
- [ ] 5.2 Manual run in a host project with `claude --plugin-dir <this repo>`: run `/sdlc-pipeline:build-use-case` on a small use case. Check that the retrospective's front matter has `claude_code`, `orchestrator` and an `agents` line for every agent type that ran, with full model IDs matching the session report's Model column. Check that no value was filled from frontmatter, so any agent whose transcript lacks effort shows `unknown`.
- [ ] 5.3 In the same host project, add a `retrospectives/TEMPLATE.md` without the new fields and repeat a short run, e.g. stop at Gate 1. Check that the retrospective still has the fields and `TEMPLATE.md` is unchanged.
