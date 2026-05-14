---
name: generate-issue-reports
description: Particiona o raw-issues.json em relatórios paralelizáveis (um por arquivo), enriquecendo com linguagem detectada, contexto de código, severidade Clean Code (INFO/LOW/MEDIUM/HIGH/BLOCKER) e agente especialista recomendado.
---

# Skill: generate-issue-reports

Transforma `.sonar-reports/raw-issues.json` em múltiplos relatórios Markdown — **um por arquivo** — prontos para serem entregues a especialistas individuais em paralelo.

## Por que um relatório por arquivo?

Dois especialistas editando o mesmo arquivo geram conflito. Particionar por arquivo garante isolamento natural: cada unidade de trabalho mexe num arquivo único. Isso torna a fase de fix trivialmente paralelizável (em sessões/processos distintos) e auditável.

## Inputs

- `.sonar-reports/raw-issues.json` (gerado por `fetch-codesmells`)
- `.sonar-reports/session.json` (apenas para metadados — referenciado nos relatórios)

## Passos

### 1. Carregar e validar

Leia `raw-issues.json`. Se `total_after_local_filter == 0`, escreva um INDEX.md vazio com explicação e termine sem gerar relatórios.

### 2. Agrupar issues por `file_path`

Para cada grupo, calcule:
- Contagem total de issues
- Distribuição de severidades (taxonomia Clean Code: `BLOCKER | HIGH | MEDIUM | LOW | INFO`)
- Distribuição de `impactSoftwareQualities` (esperado: todas `MAINTAINABILITY`)
- Regras únicas presentes (`rule`)
- Linguagem detectada
- Agente recomendado
- **Funções/classes tocadas** (informativo): se o arquivo existir localmente, extraia heuristicamente o identificador de função/classe que contém cada linha da issue. Heurística simples: escanear de baixo para cima a partir da linha da issue procurando padrões idiomáticos da linguagem (`def `, `function `, `class `, `func `, `public ... (`, etc.). Não falhe se não encontrar — apenas omita.

### 3. Tabela de mapeamento linguagem → agente

| `language` (Sonar) / extensão | `recommended_agent`    |
| ----------------------------- | ---------------------- |
| `py`                          | `python-expert`        |
| `ts`, `tsx`                   | `typescript-expert`    |
| `js`, `jsx`, `web`            | `typescript-expert`    |
| `java`                        | `java-expert`          |
| `cs`                          | `csharp-expert`        |
| `go`                          | `go-expert`            |
| qualquer outro                | `generic-expert`       |

### 4. Agrupar arquivos por **módulo**

A unidade atômica de edição é o **arquivo** (deliberadamente, para garantir paralelismo sem conflito — dois especialistas no mesmo arquivo sempre colidem, então segmentar abaixo do arquivo não ajuda no paralelismo).

Acima do arquivo, agrupamos por **módulo** para fornecer uma visão estratégica no `PLAN.md`. Detecção de módulo (em ordem de precedência):

1. **Subprojeto** (monorepos): se `<dir-pai-mais-próximo-com-package.json/pom.xml/build.gradle/go.mod/Cargo.toml/pyproject.toml>` ≠ raiz, esse diretório é o módulo.
2. **Diretório imediato** do arquivo (default): para `src/api/users.py` → módulo `src/api`.
3. **Raiz** (`.`) para arquivos diretos na raiz.

### 5. Extrair contexto de código

Para cada issue, leia 3 linhas antes e 3 depois da linha reportada do arquivo no disco (se o arquivo existir localmente). Se não existir, marque `[arquivo não encontrado localmente — pode ser um caminho remoto/CI]`.

### 6. Numerar e ordenar relatórios

Numere sequencialmente: `REPORT-001`, `REPORT-002`, ... Ordene por:
1. Maior número de issues `BLOCKER` no arquivo, depois
2. Maior número de issues `HIGH`, depois
3. Maior número total de issues

(arquivos mais críticos primeiro — mais útil em sessões com `max_issues` apertado)

### 7. Gerar slug

Substitua `/` por `__`, remova extensão, limite a 40 chars.
Ex: `src/api/users.py` → `src__api__users`

### 8. Escrever os artefatos

Três níveis de saída:

- `.sonar-reports/PLAN.md` — plano de alto nível segmentado por módulo
- `.sonar-reports/reports/REPORT-<NNN>-<slug>.md` — relatórios atômicos (1 por arquivo)
- `.sonar-reports/reports/INDEX.md` — tabela linear para o dispatch

## Template do relatório individual

```markdown
# REPORT-<NNN> — <file_path>

**Linguagem:** <language>
**Especialista recomendado:** <recommended_agent>
**Total de issues:** <N>
**Distribuição de severidade:** BLOCKER: 0, HIGH: 2, MEDIUM: 5, LOW: 1, INFO: 0
**Qualidade impactada:** MAINTAINABILITY (code smells — Clean Code taxonomy)
**Esforço estimado (Sonar):** <soma de efforts>

**Contexto da sessão Sonar:**
- Project: `<project_key>`
- Escopo: `<OVERALL | NEW_CODE/PR | NEW_CODE/BRANCH>`
- PR/Branch: `<id ou nome>`

## Como este relatório deve ser tratado

Este relatório é uma **unidade atômica de trabalho** para o agente `<recommended_agent>`.
O agente deve resolver todas as issues abaixo em uma única passada e gerar um arquivo
`REPORT-<NNN>-<slug>.fix.md` no mesmo diretório ao terminar.

## Issues

### Issue 1 — <rule_key> (severidade: <HIGH>)

- **Linha:** <line>
- **Issue key:** <key>
- **Mensagem do Sonar:** <message>
- **Tags:** <tags ou "-">
- **Esforço estimado:** <effort>
- **Criada em:** <creation_date>

**Contexto:**
```
<arquivo>:<line-3>    <linha de código>
<arquivo>:<line-2>    <linha de código>
<arquivo>:<line-1>    <linha de código>
<arquivo>:<line>      ← AQUI
<arquivo>:<line+1>    <linha de código>
<arquivo>:<line+2>    <linha de código>
<arquivo>:<line+3>    <linha de código>
```

### Issue 2 — ...

(uma seção por issue, ordenadas por linha crescente)

## Arquivo completo

O agente especialista deve `view` o arquivo `<file_path>` completo antes de editar.
Recomenda-se aplicar edições da última linha para a primeira para evitar drift de offsets.

## Consulta opcional à regra do Sonar

Se a mensagem do Sonar não for suficiente, o especialista pode consultar detalhes
da regra via tool MCP `show_rule` passando o `rule key` (ex: `python:S3776`).
```

## Template do PLAN.md

```markdown
# Plano de Limpeza — <project_key>

**Sessão:** [.sonar-reports/session.json](session.json)
**Gerado em:** <timestamp ISO>
**Escopo:** <OVERALL | NEW_CODE/PR-142 | NEW_CODE/BRANCH-main>
**Total de issues:** 23
**Total de arquivos afetados:** 7
**Total de módulos afetados:** 3

## Estratégia de segmentação

A **unidade atômica de edição é o arquivo** (um especialista por arquivo) — isso garante
edições independentes sem conflito de merge. Abaixo do arquivo (funções/classes), a
segmentação seria contraproducente para paralelismo: dois especialistas no mesmo arquivo
colidem mesmo que toquem funções diferentes.

Acima do arquivo, agrupamos por **módulo** (diretório / subprojeto) para você visualizar a
estratégia em camadas, priorizar e revisar.

## Módulos

### 📦 Módulo: `src/api` (Python)

**Issues:** 12 | **Arquivos:** 3 | **Pior severidade:** HIGH

| Arquivo               | Issues | Pior sev | Funções/classes tocadas                          | Relatório → Especialista          |
| --------------------- | ------ | -------- | ------------------------------------------------ | --------------------------------- |
| src/api/users.py      | 8      | HIGH     | `authenticate`, `_validate_user`, `UserService`  | REPORT-001 → `@python-expert`     |
| src/api/auth.py       | 3      | MEDIUM   | `login`, `refresh_token`                         | REPORT-002 → `@python-expert`     |
| src/api/posts.py      | 1      | LOW      | `list_posts`                                     | REPORT-003 → `@python-expert`     |

### 📦 Módulo: `src/components` (TypeScript)

**Issues:** 8 | **Arquivos:** 2 | **Pior severidade:** HIGH

| Arquivo                       | Issues | Pior sev | Funções/classes tocadas               | Relatório → Especialista              |
| ----------------------------- | ------ | -------- | ------------------------------------- | ------------------------------------- |
| src/components/Form.tsx       | 5      | HIGH     | `Form`, `useFormValidation`           | REPORT-004 → `@typescript-expert`     |
| src/components/Table.tsx      | 3      | MEDIUM   | `Table`, `renderRow`                  | REPORT-005 → `@typescript-expert`     |

### 📦 Módulo: `backend/services` (Java)

**Issues:** 3 | **Arquivos:** 2 | **Pior severidade:** MEDIUM

| Arquivo                                      | Issues | Pior sev | Funções/classes tocadas        | Relatório → Especialista     |
| -------------------------------------------- | ------ | -------- | ------------------------------ | ---------------------------- |
| backend/services/UserService.java            | 2      | MEDIUM   | `UserService`, `findById`      | REPORT-006 → `@java-expert`  |
| backend/services/AuthService.java            | 1      | LOW      | `AuthService`                  | REPORT-007 → `@java-expert`  |

## Ordem sugerida de despacho

Critérios: BLOCKERs primeiro, depois HIGH, depois total de issues.

| # | Relatório   | Arquivo                          | Pior sev | Issues |
| - | ----------- | -------------------------------- | -------- | ------ |
| 1 | REPORT-001  | src/api/users.py                 | HIGH     | 8      |
| 2 | REPORT-004  | src/components/Form.tsx          | HIGH     | 5      |
| 3 | REPORT-002  | src/api/auth.py                  | MEDIUM   | 3      |
| 4 | REPORT-005  | src/components/Table.tsx         | MEDIUM   | 3      |
| 5 | REPORT-006  | backend/services/UserService.java | MEDIUM  | 2      |
| 6 | REPORT-003  | src/api/posts.py                 | LOW      | 1      |
| 7 | REPORT-007  | backend/services/AuthService.java | LOW     | 1      |

## Como executar em paralelo

Cada relatório acima toca um arquivo distinto — eles são **independentes por construção**.
Para paralelismo real, abra terminais separados e dispare um especialista por terminal.
Veja [INDEX.md](reports/INDEX.md) para os comandos prontos.
```

## Template do INDEX.md

```markdown
# Sonar Code Cleaner — Índice de Relatórios

**Sessão:** [.sonar-reports/session.json](../session.json)
**Gerado em:** <timestamp ISO>
**Escopo:** <OVERALL | NEW_CODE/PR-142 | NEW_CODE/BRANCH-main>
**Project key:** <project_key>
**Total de relatórios:** <N>
**Total de issues:** <M>

## Distribuição

| Severidade | Quantidade |
| ---------- | ---------- |
| BLOCKER    | 0          |
| HIGH       | 4          |
| MEDIUM     | 15         |
| LOW        | 4          |
| INFO       | 0          |

| Linguagem | Issues | Arquivos | Especialista          |
| --------- | ------ | -------- | --------------------- |
| py        | 12     | 3        | @python-expert        |
| ts        | 8      | 2        | @typescript-expert    |
| java      | 3      | 2        | @java-expert          |

## Tabela de despacho

| #  | Relatório                              | Arquivo                          | Lng  | Iss | Pior sev | Especialista          |
| -- | -------------------------------------- | -------------------------------- | ---- | --- | -------- | --------------------- |
| 01 | REPORT-001-src__api__users.md          | src/api/users.py                 | py   | 8   | HIGH     | @python-expert        |
| 02 | REPORT-002-src__components__Form.md    | src/components/Form.tsx          | ts   | 5   | MEDIUM   | @typescript-expert    |
| ...                                                                                                                            |

## Fluxo de dispatch

O orquestrador (ou o usuário) percorre esta tabela e para cada linha invoca o especialista
indicado, passando o caminho do relatório como input. Cada despacho pode ocorrer em paralelo
em sessões separadas — os relatórios são independentes por design (um arquivo por relatório).
```

## Saída

- 1 arquivo `.sonar-reports/PLAN.md` (visão estratégica por módulo)
- N arquivos `.sonar-reports/reports/REPORT-<NNN>-<slug>.md` (unidades atômicas)
- 1 arquivo `.sonar-reports/reports/INDEX.md` (tabela linear para dispatch)
- Resumo impresso para o orquestrador

## Tratamento de erros

| Erro                              | Ação                                                          |
| --------------------------------- | ------------------------------------------------------------- |
| `raw-issues.json` não existe      | Pedir para rodar `fetch-codesmells` antes                     |
| `raw-issues.json` vazio           | Avisar; gerar INDEX.md com explicação; não gerar relatórios   |
| Arquivo do projeto não encontrado | Gerar relatório mesmo assim, com aviso de "contexto indisponível" |
| Conflito de nome de relatório     | Sufixar com hash curto                                        |
