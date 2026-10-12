## 1. Profile template

- [ ] 1.1 In `templates/sdlc-profile.md`, add the optional **Package manager** line under Commands (design D4) and change the Verify example to `pnpm test, ./gradlew build`. Verify the line says agents install and run scripts only with it, and that deleting it is allowed for projects without a `package.json`

## 2. init

- [ ] 2.1 In `skills/init/SKILL.md` step 1, give the OpenSpec install command as `pnpm add -g @fission-ai/openspec`, with `npm install -g @fission-ai/openspec` as the fallback. Verify against the "install hints prefer pnpm" requirement
- [ ] 2.2 In step 2, add a **Package manager** bullet: if there is a `package.json`, pick the manager in the D2 order, write the Package manager line, and use that manager in the Verify and Code generation commands; if pnpm is picked and `pnpm --version` fails, tell the user to run `corepack enable pnpm`; with no `package.json`, delete the line. Verify each scenario of "Init records the project's package manager, preferring pnpm" maps to the wording
- [ ] 2.3 In step 7 (Report), add: when the manager isn't pnpm, recommend moving with the D3 steps (`pnpm import`, remove the old lockfile, set `packageManager`, update CI, update the profile); when a pnpm lockfile sits beside an npm or yarn one, say the other looks stale. State that `init` changes none of these files. Verify against "Init recommends moving to pnpm but never migrates" and both its scenarios

## 3. Docs and config

- [ ] 3.1 In `README.md` Prerequisites, give the pnpm install command first, the npm one as fallback, and note `pnpm setup` is needed once for global installs. Verify `git grep -n "npm install -g @fission-ai"` shows it only as a fallback
- [ ] 3.2 In `docs/profile.md`, add a **Package manager** row to the Commands table (who reads it, what it means, how `init` picks it, that it's optional). Verify the table renders
- [ ] 3.3 In this repo's `openspec/config.yaml`, add the D1 exception to the stack-agnostic constraint. Verify `scripts/validate.py` still lists `pnpm` in `STACK_NAMES`
- [ ] 3.4 Add a `[0.7.0]` entry to `CHANGELOG.md` (init prefers pnpm for JavaScript projects; new optional Package manager profile line; host projects need do nothing, and can add the line by hand) and bump the version to `0.7.0` in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Verify the versions match

## 4. Verification

- [ ] 4.1 Run `python3 scripts/validate.py` and `claude plugin validate .` and verify both pass
- [ ] 4.2 With `claude --plugin-dir <this repo>`, run `/sdlc-pipeline:init` in three scratch projects with no profile: (a) a `package.json` with a `test` script and no lockfile, (b) the same with `package-lock.json`, (c) no `package.json`. Check: (a) Package manager pnpm and a pnpm Verify command; (b) Package manager npm, npm commands, a migration recommendation in the report and `package-lock.json` unchanged; (c) no Package manager line and no pnpm anywhere in the profile
