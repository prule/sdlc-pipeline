# sdlc-pipeline

A Claude Code plugin that turns a **business use case** into reviewed, tested and archived code
through a team of specialised agents, with two human approval gates. Every run leaves a
retrospective and a session report behind, so you can see what it did and improve it.

```
use case ─▶ architect ─▶ spec-reviewer ─▶ 🚦 GATE 1 ─▶ junior-dev ─▶ qa ─▶ senior-dev ─▶ 🚦 GATE 2 ─▶ archive ─▶ 📝 retro
            (plan)       (plan gate)      (you)        (implement)  (verify) (code review)  (you)
```

The planning and bookkeeping run on [OpenSpec](https://github.com/Fission-AI/OpenSpec). The plugin
doesn't assume a stack: the agents bring the roles and the judgment, and each project brings its own
stack rules in a short **profile** file (`.claude/sdlc-profile.md`).

## Contents

| Component | Name | What it does |
|-----------|------|--------------|
| Skill | `/sdlc-pipeline:init` | Sets a project up: checks OpenSpec, writes the profile, creates the folders. |
| Skill | `/sdlc-pipeline:write-use-case <idea>` | Interactively drafts a business use case from the domain docs and saves it to `use-cases/`. |
| Skill | `/sdlc-pipeline:build-use-case <path>` | Runs the whole pipeline for one use case, with the two gates, fix loops, budget caps and the retrospective. |
| Skill | `session-report` | Turns a session log into an HTML report (agent timeline, gate value, errors, context use). Ask *"analyse this session"*. |
| Agent | `architect` | Use case → OpenSpec change (proposal, design, spec delta, tasks). |
| Agent | `spec-reviewer` | Read-only plan gate: standards conformance + design soundness. |
| Agent | `junior-dev` | Implements `tasks.md` and stays inside the plan. |
| Agent | `qa` | Checks every requirement has a test, runs the suite, reports evidence. |
| Agent | `senior-dev` | Final code review; fixes what it finds and hands design calls back. |
| Agent | `use-case-writer` | One-shot use-case drafting (the non-interactive `write-use-case`). |
| Hooks | `hooks/hooks.json` | Logs every tool call and agent event to `logs/pipeline-events.jsonl` in the project. |
| Script | `scripts/pipeline-report.py` | Renders that event log as an HTML dashboard. |
| Templates | `templates/` | Profile, use case, retrospective, retrospectives README. |

Agents show up namespaced, for example `sdlc-pipeline:architect` in `/agents`, and you can run one
by itself: *"Use the sdlc-pipeline:qa agent to verify add-product-search"*.

## Prerequisites

- [Claude Code](https://code.claude.com) with plugin support.
- The **OpenSpec CLI** (`npm install -g @fission-ai/openspec`), initialised in the project
  (`openspec init`), so that `openspec/config.yaml` and the `opsx:*` / `openspec-*` skills exist.
- **Python 3.8+** for the hooks and reports (standard library only).
- Recommended: a `domain/` folder (glossary, business rules, bounded contexts, actors, overview) and
  a `standards/` folder. The agents ground their work in these. Without them the pipeline still
  runs, but its plans are only as good as the use case.

## Install

**For a team (recommended):** add this to the project's checked-in `.claude/settings.json`. Teammates
who trust the folder are asked to install the plugin the first time they open it.

```json
{
  "extraKnownMarketplaces": {
    "sdlc-pipeline": { "source": { "source": "github", "repo": "prule/sdlc-pipeline" } }
  },
  "enabledPlugins": { "sdlc-pipeline@sdlc-pipeline": true }
}
```

**Just for you:**

```
/plugin marketplace add prule/sdlc-pipeline
/plugin install sdlc-pipeline@sdlc-pipeline
```

### Recommended project settings

Plugins can't set environment variables or permissions, so put these guardrails in the project's
`.claude/settings.json` yourself:

```json
{
  "env": {
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "16000",
    "MAX_THINKING_TOKENS": "12000",
    "BASH_DEFAULT_TIMEOUT_MS": "180000",
    "BASH_MAX_TIMEOUT_MS": "600000"
  },
  "permissions": {
    "defaultMode": "acceptEdits",
    "deny": ["Bash(<your publish/deploy command>:*)"]
  }
}
```

## Quick start

```
/sdlc-pipeline:init                                   # once per project: profile + folders
/sdlc-pipeline:write-use-case <rough idea>            # draft use-cases/UC-<n>-<slug>.md, then review it
/sdlc-pipeline:build-use-case use-cases/UC-003-….md   # run the pipeline; answer the two gates
```

`build-use-case` creates a `feat/uc-<n>-<slug>` branch from your base branch (as the profile says),
runs the agents, stops for your approval at Gate 1 (the plan) and Gate 2 (the finished change), then
writes `retrospectives/<date>-<change>.md` and `reports/sessions/<session>.report.html`. Commit both
with the change and open the PR.

## Documentation

- **[docs/pipeline.md](docs/pipeline.md)**: the stages, gates, fix loops, budget guardrails and
  retrospectives, and how to run any phase by hand.
- **[docs/profile.md](docs/profile.md)**: the project profile, field by field, with a worked example.
- **[docs/observability.md](docs/observability.md)**: the event-log hooks, the pipeline dashboard
  and session reports.
- **[docs/evaluating-the-pipeline.md](docs/evaluating-the-pipeline.md)**: how to tell whether the
  pipeline, and each agent and doc in it, is earning its place, including A/B ablations.
- **[skills/session-report/README.md](skills/session-report/README.md)**: the report generator in
  full.
- **[CHANGELOG.md](CHANGELOG.md)**.

## Updating

Claude Code checks the marketplace for a new `version` and updates the plugin. To update now, run
`/plugin marketplace update sdlc-pipeline`, then restart Claude Code. Project-owned files (the
profile, use cases, retrospectives) are never touched by an update. Read the CHANGELOG for anything
that asks you to change the profile.

## Developing the plugin

```bash
git clone https://github.com/prule/sdlc-pipeline ~/projects/sdlc-pipeline
cd <a project that uses it>
claude --plugin-dir ~/projects/sdlc-pipeline    # this session uses your working copy
```

Changes to agents, skills and hooks take effect in the next session. Before you push, run the same checks CI runs:

```bash
python3 scripts/validate.py          # manifests, frontmatter, Python syntax, version sync
claude plugin validate .             # Claude Code's own manifest check
```

Retrospective recommendations that target an agent or skill belong here, as an issue or a PR. Ones
that target a standard, the profile or the domain docs belong in the project.

### Releasing

1. Bump `version` in `.claude-plugin/plugin.json` **and** `.claude-plugin/marketplace.json` (the
   validate script checks they match). Use semver: a profile change that projects must make is a
   minor version before 1.0, a major one after.
2. Add a CHANGELOG entry.
3. Commit, tag `vX.Y.Z`, and push with tags. Installed copies pick up the new version on their next
   update.

## License

MIT. See [LICENSE](LICENSE).
