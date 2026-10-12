## Context

`init` step 2 drafts the profile's Commands from whatever build files it finds (`package.json`
scripts, Gradle, Maven…) and asks the user only for what it can't find. The profile template's Verify
example reads `npm test, ./gradlew build`. `init` step 1 and the README tell people to run
`npm install -g @fission-ai/openspec`. No agent knows which package manager a project uses except by
reading the Verify command. See proposal.md for motivation and specs/project-setup/spec.md for the
requirements.

This repo's constraint: agents, skills and catalogue templates never name a language, build tool or
framework. `validate.py` enforces it for `templates/standards/` only. `init` already names build files
for detection, so detection-level names in `init` have precedent; a *preference* for one tool does
not.

## Goals / Non-Goals

**Goals:**
- New JavaScript projects get pnpm commands in their profile without anyone asking.
- Existing npm or yarn projects keep working commands and get a clear recommendation to move.
- Agents use the project's package manager, so they never create a second lockfile.

**Non-Goals:**
- Migrating a project to pnpm. That changes the lockfile and CI, so it belongs in a use case or a
  person's hands.
- A pnpm rule in the standards catalogue. The catalogue stays stack-agnostic and `pnpm` stays on
  `validate.py`'s banned list.
- Changing any agent prompt.
- Switching this repo's CI to pnpm. CI installs one global tool; pnpm there would add a setup step
  for no gain.

## Decisions

### D1. The preference lives in `init` and the profile template, as a stated exception

The stack-agnostic constraint in `openspec/config.yaml` gains one exception: *"`init` and the profile
template prefer pnpm for JavaScript projects."* Everything else stays neutral.

*Why:* the profile is where stack facts belong, and `init` is what writes it. Putting the preference
there steers every new project once, at setup, and leaves the agents and the catalogue untouched.

*Alternative:* a catalogue standard ("use pnpm"). Rejected: it breaks the catalogue's rule and
`validate.py`'s check, and a standard can't choose the Verify command anyway.
*Alternative:* the agents prefer pnpm. Rejected: agents would have to second-guess the profile, and
on an npm project they would break the build.

### D2. Detection order: explicit field, then lockfile, then pnpm

1. `packageManager` in `package.json` (Corepack's field: an explicit choice by the project);
2. `pnpm-lock.yaml`;
3. `package-lock.json` → npm, `yarn.lock` → yarn;
4. no lockfile → pnpm.

*Why:* an explicit field or an existing lockfile is a decision the project already made, and the
commands must match it to work. Only when nothing has been decided does the preference apply.
pnpm's lockfile wins over a stray npm one because a pnpm lockfile is rarely there by accident.

### D3. Recommend, never migrate

For an npm or yarn project, `init`'s report adds a short recommendation with the steps: run
`pnpm import` to convert the lockfile, delete the old lockfile, set `packageManager`, update CI, then
update the profile's Package manager and commands. `init` changes none of these.

*Why:* `init` never overwrites existing files, and a lockfile migration changes resolved versions,
so it needs a person to review it and a green build.

### D4. A Package manager line in the profile template

```markdown
- **Package manager:** `<pnpm | npm | yarn, or delete this line if the project has no package.json>`.
  Agents install dependencies and run scripts only with this; they never create another lockfile.
```

The Verify example changes from `npm test, ./gradlew build` to `pnpm test, ./gradlew build`.

*Why:* every agent already reads the whole profile, so a line that states its own rule reaches them
without a prompt change. It is optional, so existing profiles stay valid.

### D5. Install hints

`init` step 1 and the README Prerequisites say: install the CLI with
`pnpm add -g @fission-ai/openspec` (or `npm install -g @fission-ai/openspec`). pnpm's global installs
need `pnpm setup` once; the README says so in the same line.

## Risks / Trade-offs

- [pnpm isn't installed on the user's machine] → the profile's commands fail on first run. `init`
  checks `pnpm --version` when it picks pnpm, and if it's missing tells the user to enable it with
  `corepack enable pnpm` before running the pipeline.
- [The exception weakens the stack-agnostic rule] → it is written down as one named exception in
  `openspec/config.yaml`, and `validate.py` still bans `pnpm` in the catalogue.
- [Agents ignore the Package manager line] → it sits under Commands next to Verify, which agents
  already follow; the manual check in tasks looks for a second lockfile after a run.

## Migration Plan

None. Existing profiles are never rewritten. Rollback is reverting the release.
