---
name: feature-builder
description: >
  Implementa uma feature a partir de spec, plano e casos de teste, dividindo cada fase
  em unidades independentes de implementação e testes, com contexto mínimo e modelo
  configurável para testes. Detecta a stack, coordena especialistas em paralelo ou em
  sequência, commita por fase e atualiza o roadmap após a verificação dos critérios de
  aceite. Use para implementar feature, executar plan.md ou retomar implementação.
---

# Feature Builder

Autonomously implement a feature from its existing `spec.md` + `plan.md` + `tests.md`. The skill reads the feature's technical specification, implementation plan and test-case specification, detects the technology stack, delegates the coding work to the matching technology specialist, validates each phase, commits, updates `.sdd-builder/prd_map_progress.json`, and reports results against the acceptance criteria declared in the PRD.

A execução usa unidades delimitadas: implementação com o especialista da stack e autoria/execução de testes com `sdd-test-specialist`. Leia [Execução por unidades independentes](references/parallel-execution.md) para opções, dependências, despacho e escolha de modelo. Workers usam apenas o contrato da skill [work-unit](../work-unit/SKILL.md), sem carregar este fluxo completo.

This is **Step 3 of the SDD journey** and the only skill allowed to move a feature to `in-progress` or `done` in the roadmap.

## INPUT

Free-form. The skill figures out what was passed. Any combination works:

- A feature identifier: `F09`, `Session Control`, or similar.
- A feature folder: `.sdd-builder/F09-session-control-file-transfer/`, `./F09/`, etc.
- A file inside the feature folder: `.sdd-builder/F09-session-control-file-transfer/spec.md`.
- A PRD path: `@.sdd-builder/PRD.md`, `sdd-builder/PRD.md`, `@PRD.md`.
- Extra natural-language instructions appended anywhere (see **Overrides**).
- Opções por execução: `execution=parallel|sequential`, `max-workers=N`, `test-model=inherit|<ID disponível no host>`. São instruções da skill, não flags de CLI.

The skill only needs to locate three files and one reference source:

1. **`spec.md` and `plan.md`** for the target feature. If the input points to a folder, look inside. If it points to a file, look in its parent folder. If it points to an ID or name, search under `.sdd-builder/` for a folder matching `<ID>-*` or whose name kebab-cases to the given name.
2. **`tests.md`** in the same folder. Optional but expected: when absent, note it under soft-fails and derive tests from the spec's Testing Strategy instead.
3. **The PRD**. If explicitly passed, use it. Otherwise, auto-discover: `.sdd-builder/PRD.md` → `PRD.md` → any top-level `*.md` whose content reads like a product spec. If none found, abort. If multiple are plausible, abort and list them.

## OUTPUT

- **Commits**: one per phase of `plan.md`, on the current branch (no branch creation, no branch switching).
- **Roadmap update**: the feature's `status` in `.sdd-builder/prd_map_progress.json` moves to `in-progress` when work starts and to `done` only when Step 8 says the run succeeded.
- **Chat report** at the end: the feature's acceptance-criteria checklist marked ✓ / ✗ / — against actual test results, plus sections for Deviations, Soft-fails, Pre-existing failures, Overrides applied, Overrides ignored, and Phase status.
- **Resumo de execução**: modos solicitado/efetivo, unidades por fase, limite de workers, modelos de teste solicitado/efetivo e fallbacks. O quadro de unidades fica em memória ou nas tarefas do host.

Não crie artefatos extras de planejamento no projeto alvo: o quadro de unidades e o relatório ficam nas tarefas do host/chat. Além do código, testes, roadmap e commits, comandos podem gerar seus artefatos usuais de build/teste nos diretórios autorizados; não os inclua no commit por padrão.

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
| `execution=parallel` | `execution=sequential`, "modo sequencial", "no parallel" |
| `max-workers=3` | `max-workers=2`, "no máximo 2 agentes" |
| `test-model=inherit` | `test-model=haiku` (quando disponível), "use o modelo X nos testes" |

For each recognized override, record before/after for the final report's "Overrides applied" section.

**Immutable core (cannot be overridden):** the final AC checklist and its traceability to the PRD, and the roadmap update. Instructions that would disable either are logged under "Overrides ignored" with the reason.

Ambiguous or contradictory instructions → default wins; logged under "Overrides ignored" with "ambiguous, kept default".

Para as opções de execução, aplique a precedência e os fallbacks da [referência](references/parallel-execution.md): proibição explícita de subagentes/paralelismo prevalece; seleção de modelo só vale quando aplicada pelo host. `skip tests` limita a execução por fase, mas não dispensa a verificação final obrigatória do Step 8.

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
| Swift / SwiftUI | `Package.swift`, `*.xcodeproj`, `*.xcworkspace`, `Project.swift` (Tuist), `project.yml` (XcodeGen) | `sdd-swift-specialist` |

Rules:

- **Repositórios poliglotas:** selecione por unidade dentro da fase, não pela maioria dos arquivos do repositório. Registre fase/unidade → especialista; testes recebem as convenções da stack correspondente.
- **Stack ambígua ou sem especialista:** execute a unidade inline seguindo a spec e registre a limitação. A unidade inline também conta como writer para conflitos e barreiras.
- **Marcadores de mesmo peso:** escolha a stack que realmente possui os arquivos da unidade e documente a decisão; se a unidade mistura stacks independentes, divida-a.
- **User override:** an explicit "use the X specialist" instruction wins over detection.
- **Host without sub-agent dispatch** (some CLI hosts have no delegation primitive): do not fail. Apply the specialist's conventions inline yourself and state in the report that the specialist was applied inline rather than dispatched.

Selecione `sdd-test-specialist` para autoria e execução de testes em ambas as modalidades. Resolva `test-model` pela capacidade real do host antes do despacho, conforme a referência; a seleção nunca altera o modelo dos especialistas de implementação. Se a delegação aninhada estiver indisponível, mantenha a coordenação na sessão principal quando possível, ou execute inline com fallback explícito.

Cada worker recebe o contrato `work-unit`: objetivo, papel, caminhos absolutos, arquivos de leitura/escrita, dependências, recursos, trechos relevantes da spec/plano, TC/ACs, convenções locais e da stack, comandos e critério de término. Use contexto novo por unidade, sem encaminhar PRD completo, roadmap, outras fases ou histórico inteiro do chat. Retornos contêm resumo, caminhos e evidências; só carregue logs extensos quando precisar diagnosticar uma falha.

Workers não fazem stage/commit, não escrevem no roadmap e não delegam novamente. O orquestrador integra, valida, commita e acompanha o progresso.

### Step 6: Mark the feature in progress

Before the first phase runs, follow the `progress-tracker` skill to set the feature's `status` to `in-progress`, with `note` describing the run (e.g. `"implementation started from plan.md, 4 phases"`). Skip this when the roadmap is missing, and record the skip under soft-fails.

Do this once, not per phase. Keep the locked window short.

### Step 7: Execute Phases

For each phase of `plan.md`, in order:

**7.1 — Skip if already done**

Inspect the last ~20 commits on the current branch. If any commit message indicates this exact phase already ran (same feature ID + phase name or ordinal), skip the phase with status `— already committed` and move on. Detection is best-effort: match on feature ID plus normalized phase name or phase index.

**7.2 — Plan the parallelism inside the phase**

Monte o quadro de unidades seguindo [Execução por unidades independentes](references/parallel-execution.md). Separe `implementation`, `integration`, `test-authoring` e `test-execution`, com IDs, arquivos concretos, dependências, recursos e critérios de término. Confira que todo passo e caso de teste da fase tem dono. Observe o estado inicial do working tree para preservar mudanças preexistentes.

Estabilize contratos e arquivos compartilhados em unidades de integração exclusivas. Unidades paralelas precisam ter escritas disjuntas, nenhuma leitura de arquivo em alteração por outra unidade e recursos isolados. Comandos que leem o projeto inteiro aguardam a barreira de validação.

Em `parallel`, despache lotes elegíveis até `min(max-workers, slots disponíveis)`; em `sequential`, apenas uma unidade por vez. Aguarde e confira os retornos antes de liberar dependentes. Não paralelize fases nem inicie workers além da capacidade do host. Se houver dúvida sobre independência, serialize ou reagrupe.

**7.3 — Implement**

O especialista implementa somente os arquivos da sua unidade. `sdd-test-specialist` escreve os testes em unidades separadas com `test-model`. A autoria pode acompanhar a implementação apenas quando se apoia em contratos já estabilizados e não lê o código em edição. Testes embutidos no arquivo de produção exigem autoria sequencial com escopo limitado à seção de testes.

Testes escritos ficam pendentes de execução. Aguarde implementação, autoria e integração antes de executá-los contra o estado conjunto. Pedidos de mudança de contrato ou escopo voltam ao orquestrador para reagendamento; workers não editam arquivos pertencentes a outra unidade.

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

Depois que todos os writers retornarem, confira os diffs contra os escopos autorizados e despache unidades `test-execution` com `write_files` vazio e o modelo de testes selecionado. Inclua comandos, cwd e recursos exclusivos. O runner não corrige código: falha em produção volta à implementação; falha no teste volta à autoria. Aguarde cada correção e reexecute os checks afetados e a validação integrada. A contagem de retries pertence à fase e não reinicia ao trocar de worker/modelo.

- **Hard fail** = non-zero exit from lint, typecheck, or unit tests, where the failure is attributable to code this run changed. Retry up to the configured limit (default 3). Each retry reads the error, adjusts the code, re-runs. After the limit, abort the whole run and go to Step 8.
- **Soft fail** = validation cannot execute in this environment (e2e requiring browser/server not present; integration test requiring an external credential not set; suite explicitly marked non-runnable; command not found). Skip, log under `Soft-fails`, proceed.
- **Pre-existing failure** = validation fails but the failure is not attributable to code this run changed (touched unrelated files, existed on the branch before this run). Log under `Pre-existing failures`, do NOT count against the retry budget, proceed.

Warnings without non-zero exit are never failures.

Valide a fase inteira após a convergência, mesmo que checks locais tenham passado. Testes sobre o mesmo banco, cache de build, simulador ou relatórios compartilhados rodam em sequência, salvo isolamento comprovado. Registre comandos/códigos de saída e TC → AC → teste → resultado; zero casos executados, casos pulados ou mera autoria não comprovam aprovação.

**7.5 — Commit**

If validation passed (all hard fails resolved; only soft fails and pre-existing failures remain), stage only the files this phase touched and commit with a message summarizing the phase. Match the project's commit style by inspecting the last ~10 commit messages. Fallback: `feat(F<ID>): <phase name>`.

Stage specific files only (no `git add -A` / `git add .`). Commit on the current branch. Do not skip hooks. Specialists never commit — the commit is always performed here, after the whole phase converges.

Não commite enquanto houver worker ou comando ativo da fase. Preserve e exclua do stage alterações preexistentes não pertencentes à fase, inclusive quando compartilham um arquivo com a implementação.

If an override disabled commits, skip this sub-step and keep working-tree changes.

**7.6 — Proceed**

Move to the next phase. A run-level abort (hard fail past retry limit, dependency missing mid-phase) stops execution and goes to Step 8 with whatever phases already committed.

Em abort, cancelamento ou timeout, pare novos despachos e encerre/aguarde todos os workers e comandos ativos antes de verificar ou reportar. Liste unidades bloqueadas e pendentes; não deixe escritores em execução após o retorno do orquestrador.

### Step 8: Final Verification

After the last phase commits (or when the run aborted), run an independent verification pass over the whole feature before writing the report. This step exists because per-phase checks can miss regressions, and because AI commonly claims "done" when it isn't.

Com o workspace estável, delegue os comandos de testes a novas unidades `test-execution` usando `test-model`, inclusive nesta verificação final. O orquestrador continua responsável por conferir arquivos, rastreabilidade, evidências e decidir o status. Falha não autoriza o runner a editar fontes. Após correção, descarte evidências anteriores dos checks afetados e valide novamente; comandos da suíte completa podem comprovar os casos de 8.3 se identificarem cada caso no mesmo estado final.

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
- `incomplete` — há itens em `Missing from spec` (8.2 ou 8.3), unidades obrigatórias pendentes/bloqueadas ou testes/ACs sem evidência de aprovação no estado final. Registre checks pulados ou indisponíveis em Soft-fails; eles não equivalem a testes aprovados. Smoke checks seguem a exceção explícita de 8.4.
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
Execução: <solicitada> → <efetiva> | Workers: <limite solicitado/efetivo>
Modelo de testes: <solicitado> → <efetivo ou não informado pelo host>
Unidades: <ID, fase, papel, dependências, agente, estado, TC/ACs e evidências>
Fallbacks: <limitação de host/modelo/concorrência ou nenhum>
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
- Separar implementação, autoria e execução de testes em unidades com contexto mínimo; paralelizar somente quando não há conflito de escrita/leitura ou recurso e as dependências estão concluídas.
- Aplicar `test-model` pela seleção real do host e registrar solicitado/efetivo; prompt com nome de modelo não comprova troca.
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
- Deixar qualquer worker fazer stage/commit, escrever no roadmap, ampliar seu escopo ou despachar outros agentes.
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
- **Execução**: `execution=parallel`, `execution=sequential`, `run everything sequentially`.
- **Concorrência**: `max-workers=2`, `no máximo 2 agentes` (inteiro positivo; padrão 3).
- **Modelo de testes**: `test-model=inherit` (padrão), `test-model=haiku` quando o host disponibilizar esse alias. Aplica à autoria e execução, inclusive verificação final.
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

**Feature poliglota**: escolha o especialista por unidade; o relatório lista a relação fase/unidade/stack e os agentes usados.

**Host has no sub-agent dispatch**: apply the specialist conventions inline and say so in the report; never fail because delegation is unavailable.

**Conflitos inesperados entre unidades**: pare e aguarde os workers envolvidos, preserve alterações preexistentes e diffs válidos, reconcilie com um único escritor e revalide. Não faça reset/revert geral. Registre o incidente em `Deviations` e reagende as unidades afetadas em sequência.

**Modelo de testes indisponível ou sem seleção por worker**: continue com o padrão disponível e registre a preferência não aplicada e o modelo efetivo quando informado pelo host. Não afirme ter usado modelo menor sem evidência.

**Host sem concorrência ou sem delegação aninhada**: mantenha a orquestração na sessão principal quando possível; caso contrário, execute em sequência/inline e registre o modo efetivo. Testes e verificação final continuam obrigatórios.

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
