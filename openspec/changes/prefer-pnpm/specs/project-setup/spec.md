## Purpose

How `init` sets a host project up for the pipeline. This capability covers the package manager it
records for a JavaScript project, where pnpm is preferred.

## ADDED Requirements

### Requirement: Init records the project's package manager, preferring pnpm
When `init` writes a new profile for a project with a `package.json`, the profile SHALL have a
**Package manager** line, and the Verify and Code generation commands SHALL use that package manager.
The package manager SHALL be chosen in this order:
1. the manager named in `package.json`'s `packageManager` field;
2. otherwise pnpm, if a pnpm lockfile exists;
3. otherwise the manager whose lockfile exists (npm or yarn);
4. otherwise, with no lockfile, pnpm.

#### Scenario: New project with no lockfile
- **WHEN** the user runs `init` in a project with a `package.json`, a `test` script and no lockfile
- **THEN** the profile's Package manager is pnpm and its Verify command runs the tests with pnpm

#### Scenario: Project already on pnpm
- **WHEN** the project has `pnpm-lock.yaml`
- **THEN** the profile's Package manager is pnpm and `init`'s report recommends no migration

#### Scenario: packageManager field
- **WHEN** `package.json` has `"packageManager": "pnpm@9.12.0"` and there is no lockfile
- **THEN** the profile's Package manager is pnpm

#### Scenario: Not a JavaScript project
- **WHEN** the project has no `package.json`
- **THEN** the profile has no Package manager line and no pnpm command

### Requirement: Init recommends moving to pnpm but never migrates
When the chosen package manager is not pnpm, `init` SHALL keep that manager in the profile so its
commands work, and its report SHALL recommend moving to pnpm with the steps to do it. `init` SHALL NOT
delete or convert a lockfile, change `package.json`, or install anything.

#### Scenario: Project on npm
- **WHEN** the project has `package-lock.json` and no `packageManager` field
- **THEN** the profile's Package manager is npm, its commands use npm, the report recommends moving
  to pnpm with the migration steps, and `package-lock.json` is unchanged

#### Scenario: Two lockfiles
- **WHEN** the project has both `pnpm-lock.yaml` and `package-lock.json`
- **THEN** the profile's Package manager is pnpm and the report says `package-lock.json` looks stale
  and should be removed, without removing it

### Requirement: The plugin's install hints prefer pnpm
Wherever the plugin tells the user to install the OpenSpec CLI, it SHALL give the pnpm command first
and the npm command as the fallback.

#### Scenario: OpenSpec missing
- **WHEN** the user runs `init` in a project where the OpenSpec CLI is not installed
- **THEN** `init` tells the user to install it with `pnpm add -g @fission-ai/openspec`, or with npm if
  they don't use pnpm
