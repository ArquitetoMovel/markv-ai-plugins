---
name: feature-builder
description: >
  Implements a feature autonomously from its spec, plan and test-case spec, detecting the
  project stack, dispatching the matching technology specialist, committing one commit per
  phase, updating the feature roadmap and reporting results against the PRD acceptance
  criteria. Use when: implementing a spec'd feature, executing a plan.md, or resuming a
  partially implemented feature. Keywords: "implement feature", "build feature", "execute
  plan", "feature-builder".
---

# Feature Builder

Autonomously implement a feature from its existing `spec.md` + `plan.md` + `tests.md`. The skill reads the feature's technical specification, implementation plan and test-case specification, detects the technology stack, delegates the coding work to the matching technology specialist, validates each phase, commits, updates `.sdd-builder/prd_map_progress.json`, and reports results against the acceptance criteria declared in the PRD.

This is **Step 3 of the SDD journey** and the only skill allowed to move a feature to `in-progress` or `done` in the roadmap.

## INPUT

Free-form. The skill figures out what was passed. Any combination works:

- A feature identifier: `F09`, `Session Control`, or similar.
- A feature folder: `.sdd-builder/F09-session-control-file-transfer/`, `./F09/`, etc.
- A file inside the feature folder: `.sdd-builder/F09-session-control-file-transfer/spec.md`.
- A PRD path: `@.sdd-builder/PRD.md`, `sdd-builder/PRD.md`, `@PRD.md`.
- Extra natural-language instructions appended anywhere (see **Overrides**).

The skill only needs to locate three files and one reference source:

1. **`spec.md` and `plan.md`** for the target feature. If the input points to a folder, look inside. If it points to a file, look in its parent folder. If it points to an ID or name, search under `.sdd-builder/` for a folder matching `<ID>-*` or whose name kebab-cases to the given name.
2. **`tests.md`** in the same folder. Optional but expected: when absent, note it under soft-fails and derive tests from the spec's Testing Strategy instead.
3. **The PRD**. If explicitly passed, use it. Otherwise, auto-discover: `.sdd-builder/PRD.md` → `PRD.md` → any top-level `*.md` whose content reads like a product spec. If none found, abort. If multiple are plausible, abort and list them.

## OUTPUT

- **Commits**: one per phase of `plan.md`, on the current branch (no branch creation, no branch switching).
- **Roadmap update**: the feature's `status` in `.sdd-builder/prd_map_progress.json` moves to `in-progress` when work starts and to `done` only when Step 8 says the run succeeded.
- **Chat report** at the end: the feature's acceptance-criteria checklist marked ✓ / ✗ / — against actual test results, plus sections for Deviations, Soft-fails, Pre-existing failures, Overrides applied, Overrides ignored, and Phase status.

No files are written besides code changes, the roadmap entry, and commit objects. The chat report is ephemeral.

---

## EXECUTION STEPS

### Step 1: Resolve Input

Parse the entire input as free-form. Extract:

- **Feature reference**: the first token that resolves to a folder containing `spec.md` + `plan.md`. Matches: ID patterns like `F\d+`, folder paths, file paths (parent folder = target), feature names (kebab-case + fuzzy match to folder names under `.sdd-builder/`).
- **PRD reference**: an explicit `*.md` path prefixed with `@` or written literally; if it looks like a PRD (product spec content at the top), accept it. Otherwise auto-discover.
- **Extra instructions**: any remaining text that isn't a path/ID/name — treat as natural-language overrides (Step 3).

If resolution fails:

- No `spec.md` or `plan.md` in the resolved folder → abort: "spec.md/plan.md missing in `<folder>`."
- No PRD found → abort: "No PRD found. Pass the path explicitly."
- Multiple plausible PRDs → abort and list candidates.
- Ambiguous feature reference (multiple folders match) → abort and list candidates.

### Step 2: Load Context

Read in full:

- `spec.md` of the target feature — Component Overview, Data Model, API Contracts, Business Rules, UX Flows, Error Handling, Testing Strategy, Assumptions/Decisions.
- `plan.md` — phases and steps in order.
- `tests.md` — test cases, their traceability table and their expected results. This is the contract the implementation must satisfy; the AC report in Step 9 is built on top of it.
- **The PRD's acceptance-criteria content for this feature** — locate it semantically, not by section number. Typical headings: "Acceptance Criteria", "Critérios de Aceitação", "AC". Typical shape: a checkbox list `- [ ]` scoped to the feature (by ID or name). Also locate any cross-feature/integration checklist that references this feature. Do NOT assume a fixed section number — find content by its shape.
- `.sdd-builder/prd_map_progress.json` — the roadmap. If the target feature is already `done`, report it and ask whether to re-implement before doing anything. If the roadmap is missing, continue and note it under soft-fails; progress simply will not be tracked.

If the PRD has no acceptance-criteria content for this feature, proceed with an empty AC checklist and note it under soft-fails.

Do NOT explore the codebase eagerly. Open files lazily as each phase requires them.

### Step 3: Apply Overrides

Interpret extra instructions as natural-language overrides on the defaults:

| Default | Example overrides |
|---|---|
| Hard-fail retry limit = 3 | "no retry limit", "max 5 tries" |
| Fully autonomous | "pause between phases" — skill waits in chat for a reply containing `ok`, `continue`, `segue`, `yes`, or similar |
| 1 commit per phase | "single commit at the end", "no commits, just implement" |
| Run lint + typecheck + tests | "skip tests", "skip lint", "skip typecheck" |
| Implement all phases | "only phases 1 and 2", "skip phase 3" — phase positions are ordinal; labels like `A/B/C` map to `1/2/3` |
| Abort tests on external dep missing | "stub missing services", "assume empty response for missing APIs" — substitutes stubs **ONLY in test code**, never in production modules |
| Dispatch the detected specialist | "don't use subagents", "implement it yourself", "use the python specialist" |
| Parallelize independent steps | "run everything sequentially", "no parallel" |

For each recognized override, record before/after for the final report's "Overrides applied" section.

**Immutable core (cannot be overridden):** the final AC checklist and its traceability to the PRD, and the roadmap update. Instructions that would disable either are logged under "Overrides ignored" with the reason.

Ambiguous or contradictory instructions → default wins; logged under "Overrides ignored" with "ambiguous, kept default".

### Step 4: Pre-flight Dependency Check

Locate the dependency content in the PRD semantically (typical headings: "Dependency Graph", "Dependencies"; typical shape: a table or list pairing each feature with its prerequisites). For each listed dependency of the target feature, verify it appears implemented in the codebase (look for the characteristic files described in that dependency's own `spec.md` Component Overview, or obvious source-level markers).

- Any dependency missing → **abort before any implementation**. Report: "F<target> depends on F<N>, which is not implemented yet."
- All dependencies present → proceed to Step 5.

If the PRD has no dependency content, skip this step.

### Step 5: Stack Detection and Specialist Selection

Detect the technology of the files this feature will touch, then pick the specialist that owns it. Detection order: the spec's recorded technology first (`spec-builder` writes it under Technical Decisions or Assumptions), then the repository markers below, then the file extensions listed in the spec's Component Overview.

| Detected stack | Repository markers | Specialist |
|---|---|---|
| .NET / C# | `*.sln`, `*.csproj`, `*.fsproj`, `global.json`, `Directory.Build.props` | `sdd-dotnet-specialist` |
| Python | `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile`, `*.py` | `sdd-python-specialist` |
| Node / Angular / TypeScript | `package.json`, `angular.json`, `tsconfig.json`, `nx.json` | `sdd-node-angular-specialist` |
| PL/SQL / Oracle | `*.pks`, `*.pkb`, `*.plb`, `.sql` files with `CREATE OR REPLACE PACKAGE`, `liquibase`/`flyway` Oracle changelogs | `sdd-plsql-specialist` |
| Java | `pom.xml`, `build.gradle`, `build.gradle.kts`, `settings.gradle` | `sdd-java-specialist` |
| Go | `go.mod`, `go.work` | `sdd-go-specialist` |

Rules:

- **Polyglot repositories:** decide per phase, not per repository. A phase that touches only SQL packages goes to the PL/SQL specialist even in a Java monorepo. Record the mapping phase → specialist before starting.
- **Ambiguous or unsupported stack:** no specialist. Implement the phase directly, following the patterns recorded in the spec, and note "no specialist available for `<stack>`" in the report.
- **Multiple markers of equal weight:** pick the one that owns the majority of the files in the spec's Component Overview; document the choice.
- **User override:** an explicit "use the X specialist" instruction wins over detection.
- **Host without sub-agent dispatch** (some CLI hosts have no delegation primitive): do not fail. Apply the specialist's conventions inline yourself and state in the report that the specialist was applied inline rather than dispatched.

The specialist receives, in its prompt: the absolute path of the feature folder, the phase name and its steps, the relevant sections of `spec.md`, the test cases from `tests.md` that cover the phase, and the explicit constraint that it must not commit and must not write to the roadmap. Specialists implement and validate; this skill commits and tracks.

### Step 6: Mark the feature in progress

Before the first phase runs, follow the `progress-tracker` skill to set the feature's `status` to `in-progress`, with `note` describing the run (e.g. `"implementation started from plan.md, 4 phases"`). Skip this when the roadmap is missing, and record the skip under soft-fails.

Do this once, not per phase. Keep the locked window short.

### Step 7: Execute Phases

For each phase of `plan.md`, in order:

**7.1 — Skip if already done**

Inspect the last ~20 commits on the current branch. If any commit message indicates this exact phase already ran (same feature ID + phase name or ordinal), skip the phase with status `— already committed` and move on. Detection is best-effort: match on feature ID plus normalized phase name or phase index.

**7.2 — Plan the parallelism inside the phase**

Within a single phase, two steps may run in parallel only when ALL of these hold:

- Their file sets, as declared in the spec's Component Overview, are disjoint.
- Neither consumes an artifact the other creates in this same phase.
- Neither touches shared/foundational files: dependency manifests, DI or module registration, global config, routing tables, database schema and migrations, shared type definitions.

Dispatch every eligible step of the phase in a single message with multiple specialist invocations. Everything else runs sequentially, in plan order. Never parallelize across phases: phases are the commit unit and usually build on each other.

When in doubt about disjointness, run sequentially. A wrong parallel edit costs more than a slower run.

**7.3 — Implement**

Read the `spec.md` sections relevant to the phase. The specialist (or this skill, when no specialist applies) edits/creates files to fulfill the phase's steps.

**What counts as "done" for a phase** — all of the following, not just "I wrote the code":

- Every file listed for this phase in the spec's Component Overview exists and contains the described content.
- Every contract (API, schema, function signature) described for this phase matches what was written.
- Every test case in `tests.md` scoped to this phase exists and passes, or is honestly soft-failed.
- Validation in 7.4 passes (hard fails resolved).
- If the phase produces runtime behavior that isn't covered by unit tests (UI pages, server routes, migrations, CLI commands), actually exercise it before claiming done: run the dev server / build / migration / command against a local environment and confirm it behaves. If the environment can't be brought up in this run, log the runtime-check under `Soft-fails` — do NOT silently claim the phase is done.

Writing code without running it is not "done". Declaring completion without meeting the checklist above is a violation of the skill's contract.

Adapt when reality diverges from the spec (column named `pinned` in DB vs `isPinned` in spec, different component file name, slightly different path, structurally compatible types). Specs are never 100% faithful to reality — adaptation is expected. Record every adaptation in a `Deviations` list for the final report. Do NOT abort on minor divergences.

**Abort the entire run only on:**

- Dependency feature missing (usually caught in Step 4; if discovered mid-phase, abort here).
- Hard fail past the retry limit in Step 7.4 below.

Missing external dependencies needed only by *tests* (e.g., `OPENAI_API_KEY` unavailable) do NOT abort the run — they soft-fail the affected test. The implementation code that calls the service is still written.

**7.4 — Validate**

Discover validation commands at runtime: inspect `package.json` `scripts`, or for non-Node stacks inspect the equivalent (`Makefile`, `pyproject.toml`, `*.csproj`, `pom.xml`, `build.gradle`, `go.mod`, `Cargo.toml`, `vitest.config.*`, `jest.config.*`). The technology specialist knows the canonical commands for its stack — use them. Run the available ones.

- **Hard fail** = non-zero exit from lint, typecheck, or unit tests, where the failure is attributable to code this run changed. Retry up to the configured limit (default 3). Each retry reads the error, adjusts the code, re-runs. After the limit, abort the whole run and go to Step 8.
- **Soft fail** = validation cannot execute in this environment (e2e requiring browser/server not present; integration test requiring an external credential not set; suite explicitly marked non-runnable; command not found). Skip, log under `Soft-fails`, proceed.
- **Pre-existing failure** = validation fails but the failure is not attributable to code this run changed (touched unrelated files, existed on the branch before this run). Log under `Pre-existing failures`, do NOT count against the retry budget, proceed.

Warnings without non-zero exit are never failures.

When steps ran in parallel, validate the phase as a whole after all of them return, not per step. A phase is only valid when its combined output builds and passes.

**7.5 — Commit**

If validation passed (all hard fails resolved; only soft fails and pre-existing failures remain), stage only the files this phase touched and commit with a message summarizing the phase. Match the project's commit style by inspecting the last ~10 commit messages. Fallback: `feat(F<ID>): <phase name>`.

Stage specific files only (no `git add -A` / `git add .`). Commit on the current branch. Do not skip hooks. Specialists never commit — the commit is always performed here, after the whole phase converges.

If an override disabled commits, skip this sub-step and keep working-tree changes.

**7.6 — Proceed**

Move to the next phase. A run-level abort (hard fail past retry limit, dependency missing mid-phase) stops execution and goes to Step 8 with whatever phases already committed.

### Step 8: Final Verification

After the last phase commits (or when the run aborted), run an independent verification pass over the whole feature before writing the report. This step exists because per-phase checks can miss regressions, and because AI commonly claims "done" when it isn't.

Perform all of the following — no step is optional:

**8.1 — Full-suite validation**

Run the full validation suite on the entire repo (not just touched files): lint, typecheck, and the complete test suite as defined by the project. Do NOT filter to files this run changed.

- If failures appear that weren't flagged per-phase → they count as **regressions**. Attempt to fix up to the retry limit (same as hard-fail policy). If still failing, do NOT declare success — status becomes `completed with regressions` and the failures are listed under `Regressions` in the report.
- Pre-existing failures already logged in Step 7.4 stay categorized as pre-existing; they do not become regressions.

**8.2 — Component Overview walk-through**

Read the spec's Component Overview (or equivalent file-list section) and, for every file listed, verify: the file exists, its described role is visible in the content, and its contracts (exports, routes, schemas) match the spec within the adaptation rules of Step 7.3.

Any missing file, missing export, or missing contract → add to `Missing from spec` in the report. Do NOT claim success if this list is non-empty.

**8.3 — Test-case and AC re-check**

For each test case in `tests.md`, confirm a real test implements it and run it fresh right now (not just trusting that it passed in a prior phase). Then, for each acceptance criterion loaded in Step 2, use the traceability table of `tests.md` (falling back to the spec's Testing Strategy) to find the covering test cases. Mark the AC ✓ only if every covering test passes in this final re-check. If a test no longer passes → mark ✗, add to `Regressions`, and do not claim success.

Test cases in `tests.md` with no implemented test count as `Missing from spec`. ACs with no covering test remain `—` (no test).

**8.4 — Environment smoke check (when applicable)**

If the feature produces runtime surfaces that per-phase validation couldn't exercise (UI page, HTTP endpoint, migration, CLI command), do one final exercise of each against a local environment (dev server, ephemeral DB, etc.). A quick load-and-interact is enough — the goal is to catch things unit tests don't.

If the environment cannot be brought up in this run, log each skipped smoke check under `Soft-fails` — do NOT upgrade status to `success` unless every smoke check either passed or was honestly soft-failed.

**8.5 — Status decision**

The run's final status is determined by this step, not by whether phases committed:

- `success` — full suite green, every Component Overview item present, every test case implemented, every AC's test passes in 8.3, every smoke check passed or soft-failed.
- `completed with regressions` — phases committed but 8.1 or 8.3 uncovered failures that the skill couldn't resolve.
- `incomplete` — `Missing from spec` (8.2 or 8.3) is non-empty.
- `aborted at phase <N>` — run stopped during Step 7 before reaching here.

Never report `success` when any of the checks above has an unresolved failure, even if every phase individually committed clean.

### Step 9: Roadmap Update

Following the `progress-tracker` skill, write the outcome of Step 8.5 to `.sdd-builder/prd_map_progress.json`:

| Status from 8.5 | Roadmap `status` | Roadmap `note` |
|---|---|---|
| `success` | `done` | empty, or the deviations summary when relevant |
| `completed with regressions` | `in-progress` | the failing tests and why |
| `incomplete` | `in-progress` | what is missing from the spec |
| `aborted at phase <N>` | `in-progress` | the abort reason and the last committed phase |

Append any cross-cutting decision taken during implementation to `decisions`, so later features inherit the context.

This skill is the only writer of feature statuses. Technology specialists never touch this file: when steps ran in parallel, each specialist reports back and this skill performs a single write.

### Step 10: Final Report

Output the report to chat. Status comes from Step 8.5, never from "I think I finished":

```
Feature F<ID> — <name>

Status: success | completed with regressions | incomplete | aborted at phase <N>
Phases: <N> committed / <M> total
Branch: <current-branch>
Specialist: <agent used, or "none — implemented inline">
Roadmap: <feature> → <new status>

Acceptance Criteria (re-checked in Step 8.3):
✓ <AC text> (covered by <test case id> / <test name>)
✗ <AC text> (test failed after <K> retries: <error summary>)
— <AC text> (no test covers this AC)

Cross-feature integration (if any):
✓ <criterion> (covered by <test case id>)
...

Missing from spec (from Steps 8.2 and 8.3):
- <file/export/contract/test case that was required and is missing>
...

Regressions (from Step 8.1 or 8.3):
- <test name> started failing during this run: <error>
...

Deviations:
- <what was adapted and why>
...

Soft-fails:
- <what was skipped and why, including runtime smoke checks not exercised>
...

Pre-existing failures:
- <test name>: failed on entry to this run; left as-is
...

Overrides applied:
- Retry limit: 3 → unlimited
...

Overrides ignored:
- "<text>" (reason)
...

Abort reason (if status is aborted): <error>
```

If aborted, the report still lists whatever committed phases achieved and clearly marks which phase failed and why. If `completed with regressions` or `incomplete`, the report makes clear which checks failed so the user knows what to fix.

---

## RULES

**Always:**
- Require `spec.md` + `plan.md` in the target folder; abort without them.
- Load `tests.md` when present and treat its cases as the implementation contract.
- Locate AC and dependency content in the PRD semantically, never by fixed section number.
- Detect the stack and dispatch the matching technology specialist before writing code.
- Parallelize only steps inside the same phase whose file sets are disjoint.
- Commit 1 per phase (default), staging only the files that phase touched.
- Match the project's recent commit-message style.
- Adapt to minor spec/code divergences; log every adaptation under `Deviations`.
- Run validation after each phase; differentiate hard-fail (retry ≤ limit) from soft-fail (skip + log) from pre-existing failure (log, don't retry).
- Before claiming a phase is "done": confirm every file listed for that phase exists with the described content AND validation has passed. Writing code without running it is never "done".
- For phases that produce runtime surfaces (UI, HTTP route, migration, CLI), actually exercise them against a local environment before claiming done, or soft-fail the runtime check.
- Execute Step 8 (Final Verification) in full before reporting — full-suite re-run, Component Overview walk-through, test-case and AC re-check, environment smoke check.
- Derive the final status exclusively from Step 8.5. Report `success` only when every Step 8 check is green.
- Update the roadmap exactly once at Step 9, through the `progress-tracker` write protocol.

**Never:**
- Claim the run is `success` when Step 8 found regressions, missing-from-spec items, or unresolved failures — even if every phase individually committed clean.
- Skip the AC report or its traceability (immutable core).
- Skip Step 8 (Final Verification) or Step 9 (Roadmap Update).
- Let a technology specialist commit, or write to `.sdd-builder/prd_map_progress.json`.
- Parallelize steps that touch shared files (manifests, DI registration, migrations, global config) or that cross a phase boundary.
- Mark a feature `done` when the run ended in regressions, incomplete or aborted.
- Create or switch branches.
- Abort on name/path/type cosmetic divergences.
- Abort on external dependency missing for a test — soft-fail the test, keep implementing.
- Use `git add -A` or `git add .`.
- Skip git hooks.
- Count pre-existing test failures against the retry budget.
- Re-run phases already committed on the branch (detected by commit-message match).
- Insert service stubs in production modules — stubs are allowed only in test files.
- Explore the codebase upfront with a broad sweep — read files lazily as phases require.
- Declare a phase complete based only on "I wrote the files". The completion checklist in 7.3 must hold.

---

## Overrides

Free-form instructions at the end of the invocation override defaults. Examples:

- **Retry limit**: `no retry limit`, `max 5 tries`.
- **Autonomy**: `pause between phases` — waits for user reply (`ok`, `continue`, `segue`, `yes`, etc.) after each phase.
- **Commit strategy**: `no commits, just implement`; `single commit at the end`.
- **Validation**: `skip tests`, `skip lint`, `skip typecheck`.
- **Phase selection**: `only phases 1 and 2`, `skip phase 3` — phase positions are ordinal; labels `A/B/C` map to `1/2/3`.
- **Specialist**: `use the java specialist`, `don't use subagents`.
- **Parallelism**: `run everything sequentially`.
- **External services**: `stub OpenAI`, `assume empty response for missing APIs` — stubs apply ONLY in test code; production modules keep the real call.

Unrecognized or contradictory overrides: default wins; logged under `Overrides ignored`.

**Immutable core**: the AC checklist with its traceability to the PRD, and the roadmap update, cannot be overridden.

---

## Edge Cases

**No PRD found**: abort before starting.

**No spec.md or plan.md**: abort before starting.

**No tests.md**: proceed, note under soft-fails, and derive the test expectations from the spec's Testing Strategy.

**No roadmap file**: proceed with implementation, note under soft-fails, and tell the user progress is not being tracked. Do not create the roadmap from scratch — that belongs to `prd-builder`.

**Feature already `done` in the roadmap**: report it and ask whether to re-implement before touching any file.

**Dependency feature not implemented**: abort at Step 4 with a clear message.

**Ambiguous feature reference**: list candidates, abort asking which.

**Stack not covered by any specialist**: implement inline following the spec's recorded patterns; state it in the report.

**Polyglot feature (phases in different stacks)**: pick a specialist per phase; the report lists all specialists used.

**Host has no sub-agent dispatch**: apply the specialist conventions inline and say so in the report; never fail because delegation is unavailable.

**Parallel steps produce conflicting edits to the same file**: treat the phase as failed, revert the conflicting edits, re-run the phase sequentially, and record the incident under `Deviations`.

**Roadmap locked by another agent**: retry per the `progress-tracker` protocol. If the lock is stale, report it and ask before removing. Never bypass the lock silently.

**Working tree has unrelated changes at start**: proceed anyway — the skill is designed to be invokable anywhere (typically from a worktree). Commits stage only the specific files each phase touched.

**Phase name contains special characters**: fall back to `feat(F<ID>): implement phase <N>`.

**Re-invocation after a partial run**: Step 7.1 detects already-committed phases by commit-message match and skips them. Uncommitted working-tree changes from a prior interrupted run stay as-is; the skill does not clean them up.

**Hard fail past the retry limit on a step that isn't part of any AC**: abort anyway — the skill cannot judge which failures are "acceptable". User can override with `skip tests` or similar.

**External tool emits warnings, not errors**: warnings are not failures. Only non-zero exit codes count.

**Override contradicts the core contract** (e.g., `simplify the spec, drop requirements`): ignore it, log under `Overrides ignored`, proceed with the full spec.

**Validation commands not discoverable**: if the project's config files don't reveal lint/typecheck/test commands, log each missing command under `Soft-fails` and proceed.

**PRD has no AC content for this feature**: proceed with empty AC checklist and note under soft-fails.

**PRD has no dependency content**: skip Step 4 and proceed.

**Commit-message style is inconsistent in recent history**: fall back to `feat(F<ID>): <phase name>`.
