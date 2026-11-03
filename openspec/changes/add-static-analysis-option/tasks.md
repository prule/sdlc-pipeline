# Tasks

## 1. Profile setting

- [x] 1.1 Add `**Static analysis:** off` to the `## Pipeline` section of `templates/sdlc-profile.md`, after **Implementer**, worded as in design D1; verify the template still reads top to bottom.
- [x] 1.2 Document the field in `docs/profile.md`'s Pipeline table (values, default when missing, what the command must do, `qa` as its reader); verify it says the analysis server and command are the project's to provide.

## 2. QA

- [x] 2.1 In `agents/qa.md`, load the setting in procedure step 1 and add step 5 from design D2; verify the scan runs only after Verify passes and never when the setting is missing or `off`.
- [x] 2.2 Add the two rules from design D3 and the **Static analysis** line to Output (design D4); verify a scan that cannot run never blocks the verdict, and that QA still never fixes production code.

## 3. Orchestrator

- [x] 3.1 In `skills/build-use-case/SKILL.md`, add QA's Static analysis line to what Gate 2 shows; verify the orchestrator does not run the scan itself.

## 4. Docs, changelog and version

- [x] 4.1 Update `docs/pipeline.md` stage 4, Gate 2 and a short "Static analysis" section; update `README.md`'s `qa` row; verify no doc says the scan runs by default.
- [x] 4.2 Add a `## [0.9.0]` entry to `CHANGELOG.md` and bump `version` to `0.9.0` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`; verify both manifests match.

## 5. Verification

- [x] 5.1 Run `python3 scripts/validate.py`, `claude plugin validate .` and `openspec validate add-static-analysis-option --strict`; all pass.
- [ ] 5.2 In a host project with a reachable analysis server, run `claude --plugin-dir <this repo>` and `/sdlc-pipeline:build-use-case <use case>` with `**Static analysis:** \`sonar-check\``. Check: QA runs the scan once after Verify and pastes its output; a failing quality gate gives NOT READY with one defect per issue and a qa↔implementer round; the re-verify scans again; Gate 2 shows the Static analysis line.
- [ ] 5.3 In the same host project, run once with no Static analysis line. Check QA runs no scan and reports `Static analysis: off`. Then stop the server (`docker stop sonarqube`) with the scan on, and check QA reports `not run` once and its verdict does not depend on the scan.
