---
name: init
description: Set up the current project for the sdlc-pipeline plugin — check OpenSpec, write the project profile (.claude/sdlc-profile.md), and create the use-cases, retrospectives and session-reports folders. Use when the user wants to set up, initialise or onboard a project to the SDLC pipeline, or when an sdlc-pipeline agent reports a missing profile.
disable-model-invocation: true
---

Prepare this project so `/sdlc-pipeline:write-use-case` and `/sdlc-pipeline:build-use-case` can run.
**Never overwrite an existing file** — if something already exists, leave it and say so. Plugin files
live under `${CLAUDE_PLUGIN_ROOT}`.

## Steps

1. **OpenSpec.** Check `openspec --version` and that `openspec/config.yaml` exists, and that the
   OpenSpec skills are installed (`opsx:propose`, `opsx:apply`, `opsx:verify` and
   `openspec-archive-change`, usually under `.claude/skills/` and `.claude/commands/opsx/`). If any is
   missing, tell the user to install the CLI (`npm install -g @fission-ai/openspec`) and run
   `openspec init` in the project, then stop — the pipeline cannot run without it.

2. **Profile.** If `.claude/sdlc-profile.md` does not exist, create it from
   `${CLAUDE_PLUGIN_ROOT}/templates/sdlc-profile.md`. Fill in what you can find out instead of leaving
   placeholders:
   - **Commands:** the build tool (`package.json` scripts, `build.gradle(.kts)`, `pom.xml`,
     `Makefile`, `pyproject.toml`, `Cargo.toml`, `go.mod`…), and `CLAUDE.md`/`README.md` for the
     documented build, test and codegen commands. Pick the single command that compiles, tests and
     lints. If a pre-commit hook formats code, list the formatter under *Never run*.
   - **Paths:** keep the defaults unless the project already uses other folders.
   - **Git:** the base branch (`git symbolic-ref refs/remotes/origin/HEAD`, or whether a `develop`
     branch exists) and the commit style from `git log --oneline -20`.
   - **Implementation rules, Task order, Review checklist:** draft them from `standards/` (or wherever
     `CLAUDE.md` says the standards live) and `openspec/config.yaml` — one line per rule, citing the
     standard. If the project has no standards docs, leave those sections short and say so.
   - Ask the user (with `AskUserQuestion`) only for what you can't find out — usually the verify
     command and the base branch.

3. **Folders.** Create what is missing, using the profile's paths:
   - the use-cases folder (empty; the plugin's template is used unless the project adds its own
     `TEMPLATE.md`);
   - the retrospectives folder with `README.md` copied from
     `${CLAUDE_PLUGIN_ROOT}/templates/retrospectives-README.md`;
   - the session-reports folder with a `.gitkeep`.

4. **Domain and standards docs.** If the domain folder is missing, tell the user the agents rely on
   it (glossary, business rules, bounded contexts, actors and personas, overview) and suggest
   `/sdlc-pipeline:write-domain`. If the standards folder is missing, suggest
   `/sdlc-pipeline:write-standards`. Don't create either.

5. **.gitignore.** Add `logs/` (the plugin's hook writes `logs/pipeline-events.jsonl`) if it isn't
   ignored already.

6. **Team setup.** Show the user the snippet to add to the project's checked-in
   `.claude/settings.json` so teammates get the plugin automatically:

   ```json
   {
     "extraKnownMarketplaces": {
       "sdlc-pipeline": { "source": { "source": "github", "repo": "prule/sdlc-pipeline" } }
     },
     "enabledPlugins": { "sdlc-pipeline@sdlc-pipeline": true }
   }
   ```

   Offer to merge it in. Mention that plugins can't set env vars or permissions, so token caps and
   denied commands (see the plugin README, "Recommended project settings") stay in the project's
   settings.

7. **Report** what you created, what already existed, and the placeholders the user still needs to
   fill in. Suggest a reference to the profile in `CLAUDE.md` and the next step:
   `/sdlc-pipeline:write-use-case <idea>`.
