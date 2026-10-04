# retrospectives

One record per `/sdlc-pipeline:build-use-case` run, written by the orchestrator at the end of the run — including
runs that stop at a gate, escalate, or abort. They are the pipeline's memory: what the review gates
caught, why it happened, and what to change so it doesn't happen again.

- **File name:** `<YYYY-MM-DD>-<change-name>.md`, e.g. `2026-10-03-add-product-search.md`. A second
  run of the same change on the same day gets `-2`, `-3`, …
- **Format:** the plugin's [retrospective template](https://github.com/prule/sdlc-pipeline/blob/main/templates/retrospective.md)
  (copy it here as `TEMPLATE.md` to customise it for this project). Front matter for the run's facts, then the gate log, failed
  reviews, standards violations, other defects, and deduplicated recommendations.
- **What ran:** the front matter records the Claude Code version and the model and effort the
  orchestrator and each agent ran, as recorded by Claude Code (`unknown` where it recorded
  nothing). Agent frontmatter such as `model: opus` is an alias, so this is the only record of the
  actual model. Compare runs with `grep -h 'junior-dev:' retrospectives/*.md`.
- **Source:** each gate agent (`spec-reviewer`, `qa`, `senior-dev`) ends its report with a
  *Run-log findings* block (root cause and recommendation per finding); the orchestrator adds the
  human gate decisions, loop counts and escalations, and links the run's session report.

## Using them

- **After a run:** read the Recommendations. Adopt the worthwhile ones (edit the target file in a
  PR) and tick them with the PR number.
- **Every few runs:** scan the recent records for findings marked *recurs*. A finding that keeps
  coming back is a standard, rule or agent instruction that isn't working — fix the input, not the
  code.
- Records are committed with the change they describe, so the history of the pipeline and of the
  product stay together.
