# The project profile

The agents in this plugin know their roles but not your stack. They learn it from one file in your
project: **`.claude/sdlc-profile.md`**. Every agent reads it before it starts. If it is missing, the
agent stops and asks you to run `/sdlc-pipeline:init`, which drafts one from what it finds in the
project.

It is plain Markdown for the agents to read, so wording matters more than syntax. Keep the section
headings below, because the agents look for them by name. Keep each rule to one line and link to
`standards/` for the detail; the profile is an index, not a second copy.

Start from [`templates/sdlc-profile.md`](../templates/sdlc-profile.md).

## Sections

### Commands

| Field | Used by | Meaning |
|-------|---------|---------|
| **Verify** | junior-dev, qa, senior-dev | The single command that proves the code works: compile, test, lint. Agents run it after every change and paste its output as evidence. Leave out steps the agents must not run, such as a format check a hook owns. |
| **Code generation** | junior-dev | The command to run after changing a contract (OpenAPI, protobuf, GraphQL…), or `none`. |
| **Never run** | junior-dev, qa, senior-dev | Commands agents must not run: formatters owned by a hook, publish or deploy tasks. Back this up with `permissions.deny` in `.claude/settings.json`. |

### Paths

Where the pipeline reads and writes, relative to the project root. The defaults are `domain/`,
`standards/`, `use-cases/`, `retrospectives/` and `reports/sessions/`. If you change the domain or
standards folders, the session report needs `--context-dirs` to match; the skills pass it for you.

### Git

| Field | Used by | Meaning |
|-------|---------|---------|
| **Base branch** | build-use-case | The branch use-case branches are cut from. The pipeline never runs on it. |
| **Branch per use case** | build-use-case | The branch name pattern, e.g. `feat/uc-<n>-<slug>`. |
| **Pull requests target** | build-use-case | Named in the closing reminder. |
| **Commits** | everyone | The commit message convention. |

### Implementation rules

The stack rules the junior dev follows and the reviewers enforce: contract-first, layering,
migrations, test placement, error format. Cite the standard for each one.

### Task order

The order the architect writes `tasks.md` in, so the junior dev can work it top to bottom. The
spec-reviewer checks the plan follows it. If `openspec/config.yaml` also states a task order, keep
the two the same.

### Review checklist

Three lists, one per gate. Each item names a standard and what to check against it. The agents cite
these in their findings, and the retrospectives count findings per rule, so precise items here give
precise, countable findings.

- **Plan review (spec-reviewer):** what a plan must show: layering, contract shape, test plan…
- **Verification (qa):** what must be covered by a test.
- **Code review (senior-dev):** the smells and violations to reject.

### Formatting

Who formats code and when. If a hook or CI owns formatting, say so: the agents then never format,
never run the formatter and never raise formatting in a review, which stops them wasting turns on it.

## Profile, CLAUDE.md or openspec/config.yaml?

| Put it in… | When it is… |
|------------|-------------|
| `CLAUDE.md` | for **every** session, including work outside the pipeline (stack summary, conventions). |
| `openspec/config.yaml` | a rule about the **content of a planning artifact** (what a design must state, what each spec scenario needs). OpenSpec injects it while the artifact is written. |
| `.claude/sdlc-profile.md` | a fact the **pipeline agents** act on: commands, paths, branch rules, what each gate checks. |
| `standards/*.md` | the detail behind a rule, with examples and rationale. |

## Worked example

[prule/sdlc](https://github.com/prule/sdlc/blob/develop/.claude/sdlc-profile.md) is a Java 25 /
Spring Boot / Gradle REST API with contract-first OpenAPI, Clean Architecture, Flyway and
Testcontainers. Its profile is about 100 lines: a Gradle verify command that skips the hook-owned
format check, an OpenAPI generation command, six implementation rules, a seven-step task order and
a checklist per gate drawn from seven standards docs.

## Changing the profile

The profile is the cheapest place to fix a recurring retrospective finding about the stack, such as
a missed migration rule or a wrong test engine. Edit it in a normal PR. The next run picks it up;
nothing in the plugin needs to change.
