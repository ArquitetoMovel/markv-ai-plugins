# sonar-code-cleaner

> Plugin do **GitHub Copilot CLI** que orquestra a limpeza de code smells reportados pelo SonarQube/SonarCloud com um **slash command único** (`/sonar-clean`), **entrevista guiada**, **plano segmentado por módulo** e **especialistas de desenvolvimento por linguagem**.

## TL;DR

```bash
copilot plugin install ./sonar-code-cleaner
export SONARQUBE_URL=... SONARQUBE_TOKEN=... SONARQUBE_ORG=...
copilot
> /sonar-clean
```

O comando faz 5 fases ponta-a-ponta:

1. **Entrevista** — escopo (`OVERALL`/`NEW_CODE`), alvo (`projectKey`/`PR`/`branch`), severidade, limite
2. **Plano + relatórios** — chama o MCP do Sonar, gera `PLAN.md` segmentado por módulo + N relatórios atômicos por arquivo
3. **Correção em paralelo** — despacha um especialista por relatório (`@python-expert`, `@typescript-expert`, etc.); em série na mesma sessão ou em multi-sessão para paralelismo real
4. **Sumário consolidado** — `SUMMARY.md` com o que foi corrigido e o que precisa de revisão humana
5. **Atualização do README** — insere/atualiza seção de Code Quality no README do projeto (com diff e confirmação)

## Estrutura do plugin

```text
sonar-code-cleaner/
├── plugin.json                                 # manifesto (v0.3.0)
├── .mcp.json                                   # config do MCP SonarQube oficial
├── agents/
│   ├── sonar-code-cleaner.agent.md             # orquestrador principal
│   ├── python-expert.agent.md
│   ├── typescript-expert.agent.md
│   ├── java-expert.agent.md
│   ├── csharp-expert.agent.md
│   ├── go-expert.agent.md
│   └── generic-expert.agent.md
└── skills/
    ├── sonar-clean/SKILL.md                    # /sonar-clean — entry-point (NOVO em v0.3.0)
    ├── interview-user/SKILL.md                 # Fase 1: entrevista guiada
    ├── fetch-codesmells/SKILL.md               # Fase 2a: MCP search_sonar_issues_in_projects
    ├── generate-issue-reports/SKILL.md         # Fase 2b: PLAN.md + REPORT-*.md + INDEX.md
    ├── dispatch-experts/SKILL.md               # Fase 3: 1 especialista por relatório
    ├── consolidate-results/SKILL.md            # Fase 4: SUMMARY.md
    └── update-project-readme/SKILL.md          # Fase 5: README do projeto (NOVO em v0.3.0)
```

## O slash command `/sonar-clean`

**No Copilot CLI, cada skill no diretório `skills/` do plugin vira um slash command automaticamente** — o nome da skill (`sonar-clean`) é o nome do comando (`/sonar-clean`).

A skill `sonar-clean` é o **único ponto de entrada** que o usuário precisa lembrar. Ela orquestra as outras skills internas (`interview-user`, `fetch-codesmells`, etc.) na ordem certa, pausando para confirmação humana onde necessário.

### Sintaxe

```text
/sonar-clean                                    # entrevista completa
/sonar-clean PR 142 do projeto my-org_backend   # atalho: pula perguntas correspondentes
/sonar-clean overall projeto my-org_backend severidade HIGH
/sonar-clean new code do branch main, projeto my-org_backend
/sonar-clean retomar                            # reusa .sonar-reports/session.json
```

### Fluxo visual

```
/sonar-clean
   │
   ▼
┌─────────────────────────────────────────────────┐
│ [1/5] Entrevista                                │ → interview-user
│       escopo, alvo, severidade, limite          │   .sonar-reports/session.json
└─────────────────────────────────────────────────┘
   │ confirmação humana
   ▼
┌─────────────────────────────────────────────────┐
│ [2/5] Coleta + Plano                            │ → fetch-codesmells
│       MCP search_sonar_issues_in_projects       │   .sonar-reports/raw-issues.json
│       Agrupamento por módulo + por arquivo      │ → generate-issue-reports
│                                                 │   .sonar-reports/PLAN.md
│                                                 │   .sonar-reports/reports/REPORT-*.md
│                                                 │   .sonar-reports/reports/INDEX.md
└─────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────┐
│ [3/5] Correção em paralelo                      │ → dispatch-experts
│       1 especialista por relatório              │   @python-expert | @typescript-expert
│       [a] série mesma sessão                    │   @java-expert   | @csharp-expert
│       [b] multi-sessão (paralelismo real)       │   @go-expert     | @generic-expert
│                                                 │   .sonar-reports/reports/REPORT-*.fix.md
└─────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────┐
│ [4/5] Consolidação                              │ → consolidate-results
│       diff git + needs-human-review             │   .sonar-reports/SUMMARY.md
└─────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────┐
│ [5/5] Atualizar README do projeto               │ → update-project-readme
│       seção marcada + confirmação com diff      │   README.md (com confirmação)
└─────────────────────────────────────────────────┘
```

## Segmentação: por módulo, por arquivo, e a razão

A fase 2 produz **três níveis** de visão:

- **`PLAN.md`** — segmentação por **módulo** (diretório/subprojeto). Lista os arquivos do módulo, funções/classes tocadas (informativo) e a pior severidade. Esta é a visão estratégica para humanos.
- **`reports/REPORT-*.md`** — **unidade atômica de edição** (um por arquivo). É o input do especialista.
- **`reports/INDEX.md`** — tabela linear para o dispatch.

**Por que arquivo é a unidade atômica?** Dois especialistas editando o mesmo arquivo, mesmo em funções distintas, geram conflito de merge. Segmentar abaixo de arquivo não ajuda no paralelismo. Por isso a informação de função vive no PLAN.md como contexto, mas a edição é por arquivo.

## Tools do MCP do Sonar utilizados

Da documentação oficial do [`sonarqube-mcp-server`](https://github.com/SonarSource/sonarqube-mcp-server):

| Tool                                | Uso no plugin                                            |
| ----------------------------------- | -------------------------------------------------------- |
| `search_sonar_issues_in_projects`   | Tool principal — busca os code smells                    |
| `search_my_sonarqube_projects`      | Listar projetos durante a entrevista                     |
| `list_pull_requests`                | Listar PRs durante a entrevista                          |
| `get_component_measures`            | Descobrir baseline do New Code period (escopo BRANCH)    |
| `show_rule`                         | Especialistas consultam detalhe de regra (opcional)      |
| `change_sonar_issue_status`         | Marcar falsos-positivos (com confirmação explícita)      |

O toolset necessário é `issues,projects,measures,rules` (já configurado em `.mcp.json` via `SONARQUBE_TOOLSETS`).

## Filtro de code smells (taxonomia Clean Code)

- **`impactSoftwareQualities: ["MAINTAINABILITY"]`** — este plugin sempre usa esse filtro
- Severidades: `INFO | LOW | MEDIUM | HIGH | BLOCKER` (taxonomia nova)
- Status considerados: `OPEN` e `CONFIRMED` por default

## Instalação

```bash
copilot plugin install ./sonar-code-cleaner
copilot plugin list                              # confirmar instalação
```

## Configuração

Variáveis de ambiente:

```bash
# Para SonarCloud:
export SONARQUBE_URL="https://sonarcloud.io"
export SONARQUBE_TOKEN="sqa_xxxxxxxxxxxx"
export SONARQUBE_ORG="sua-org"

# Para SonarQube Server on-prem:
export SONARQUBE_URL="https://sonar.suaempresa.com"
export SONARQUBE_TOKEN="squ_xxxxxxxxxxxx"
# SONARQUBE_ORG não é necessário

# Opcional — restringe o conjunto de tools do MCP:
export SONARQUBE_TOOLSETS="issues,projects,measures,rules"
```

Para obter o token: SonarCloud em `https://sonarcloud.io/account/security`, SonarQube em `Account → Security`.

O `.mcp.json` deste plugin usa **Docker** por padrão (`mcp/sonarqube`). Se preferir outra forma de subir o MCP server, edite `.mcp.json` e reinstale o plugin.

## Uso típico

### Modo simples (uma sessão)

```text
copilot
> /sonar-clean
```

E siga as perguntas. Ao final, você terá:
- `.sonar-reports/SUMMARY.md` com tudo que foi feito
- `README.md` com uma seção de Code Quality (se você confirmar)
- Working tree do `git` com as alterações de código (sem commit automático)

### Modo paralelo (multi-sessão)

```text
# Terminal 1
copilot
> /sonar-clean
[escolha [b] paralelo na Fase 3]

# Terminais 2..N (um por relatório listado)
copilot
> @python-expert resolva .sonar-reports/reports/REPORT-001-src__api__users.md

# De volta ao Terminal 1, quando todos os *.fix.md estiverem em disco:
> /sonar-clean retomar
```

## Saídas geradas

```text
.sonar-reports/
├── session.json                                 # configuração da entrevista
├── raw-issues.json                              # dump bruto do MCP
├── PLAN.md                                      # plano estratégico por módulo
├── reports/
│   ├── INDEX.md                                 # tabela linear de despacho
│   ├── REPORT-001-<slug>.md                     # input para o especialista
│   ├── REPORT-001-<slug>.fix.md                 # output do especialista
│   └── ...
├── dispatch.log                                 # log de invocações
├── SUMMARY.md                                   # relatório executivo final
└── proposed-readme-section.md                   # (se o usuário recusou alterar o README)
```

Recomendo adicionar `.sonar-reports/` ao `.gitignore` (ou versionar só `SUMMARY.md` se quiser histórico de limpezas).

## Adicionando um novo especialista

Para suportar outra linguagem (PHP, Ruby, Kotlin, Rust...):

1. Crie `agents/<linguagem>-expert.agent.md` seguindo o padrão dos existentes
2. Atualize a tabela de mapeamento em:
   - `agents/sonar-code-cleaner.agent.md`
   - `skills/generate-issue-reports/SKILL.md`
3. Reinstale o plugin

## Mudanças por versão

### 0.3.0 (atual)

- **Novo slash command `/sonar-clean`** como entry-point único (skill `sonar-clean`)
- **Nova skill `update-project-readme`** (Fase 5): atualiza o README do projeto com seção marcada + diff + confirmação
- **`PLAN.md` segmentado por módulo** gerado pela `generate-issue-reports`, com funções/classes tocadas (informativo)
- Atalhos em linguagem natural após `/sonar-clean` para pular perguntas
- Modo `/sonar-clean retomar` para continuar uma sessão pausada

### 0.2.0

- Renomeado de `sonar-codesmell-orchestrator` para `sonar-code-cleaner`
- Skill `interview-user`: entrevista guiada (escopo, alvo, severidade)
- Tools reais do MCP: `search_sonar_issues_in_projects` etc.
- Taxonomia Clean Code: `INFO/LOW/MEDIUM/HIGH/BLOCKER` e filtro `impactSoftwareQualities: ["MAINTAINABILITY"]`
- 3 modos de coleta: Overall, New Code/PR, New Code/Branch

### 0.1.0

- Versão inicial — orquestrador + 4 fases + 5 especialistas + fallback genérico

## Limitações conhecidas

- Dentro de uma única sessão, o despacho é sequencial. Paralelismo real requer multi-sessão.
- O especialista genérico é deliberadamente conservador: muitas issues em linguagens não mapeadas são marcadas para revisão humana.
- O plugin não roda `sonar-scanner` — assume que a análise mais recente já está no Sonar.
- O escopo `NEW_CODE / BRANCH` depende de `get_component_measures` para a baseline; quando indisponível, o plugin oferece fallback explícito.
- A detecção heurística de funções/classes para o PLAN.md é informativa, não precisa — pode errar em casos exóticos (lambdas em arquivo de configuração, macros, etc.).
- Custom slash commands via diretório `commands/` ou `.github/prompts/` ainda não são suportados pelo Copilot CLI (issues #618 e #1113); por isso `/sonar-clean` é exposto via skill (que é a forma idiomática hoje).

## Referências

- [GitHub Copilot CLI plugins (oficial)](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating)
- [GitHub Copilot CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)
- [`github/copilot-plugins` marketplace](https://github.com/github/copilot-plugins)
- [`awesome-copilot` plugins](https://github.com/github/awesome-copilot/tree/main/plugins)
- [SonarQube MCP server (oficial SonarSource)](https://github.com/SonarSource/sonarqube-mcp-server)
- [SonarQube MCP server — documentação](https://docs.sonarsource.com/agent-centric-development-cycle/developer-tools/mcp-server/about-the-mcp-server)

## Licença

MIT.
