## Why

Projects set up with the plugin should use pnpm as their JavaScript package manager: it is faster,
uses less disk, and its strict dependency layout stops code from importing packages it never
declared. Today `init` copies whatever commands it finds, the profile's example says `npm test`, and
the plugin tells people to install OpenSpec with npm. Nothing steers a new project to pnpm, and
nothing tells the agents which package manager a project uses, so an agent can run `npm install` in a
pnpm project and write a second lockfile.

## What Changes

- `init` (profile step): when the project has a `package.json`, it works out the package manager from
  the `packageManager` field and the lockfile, and records it in the profile.
  - pnpm lockfile, `packageManager: pnpm@…`, or no lockfile at all → pnpm. The Verify and Code
    generation commands use `pnpm`.
  - An npm or yarn lockfile → the profile keeps that manager, so the commands keep working, and
    `init`'s report recommends moving to pnpm with the migration steps. `init` never migrates the
    project itself.
- Profile template: a new optional **Package manager** line under Commands. Agents install
  dependencies and run scripts only with it. The Verify example becomes `pnpm test`.
- Install hints: README and `init` tell people to install the OpenSpec CLI with
  `pnpm add -g @fission-ai/openspec`, with the npm command as the fallback.
- Docs: `docs/profile.md` documents the new field; `CHANGELOG.md`.
- This repo's `openspec/config.yaml`: the stack-agnostic constraint gains one stated exception,
  the package-manager preference in `init` and the profile template.

## Capabilities

### New Capabilities
- `project-setup`: what `init` records in the profile about a JavaScript project's package manager,
  and when it recommends moving to pnpm.

### Modified Capabilities
None.

## Impact

- **Components:** skills (`init`), templates (`sdlc-profile.md`), docs (`README.md`,
  `docs/profile.md`), this repo's `openspec/config.yaml`, manifests and `CHANGELOG.md`. Agents,
  the standards catalogue and `validate.py` are unchanged; `pnpm` stays on the catalogue's banned
  names list.
- **Host projects:** need do nothing. Existing profiles keep working; the Package manager line is
  optional and `init` never overwrites an existing profile. A project can add the line by hand.
  Non-JavaScript projects see no change.
- **Semver:** minor bump to 0.7.0. It changes what `init` writes and adds a profile field. No
  existing profile needs editing.
