---
name: fetch-codesmells
description: Lê .sonar-reports/session.json e chama o MCP do SonarQube (search_sonar_issues_in_projects) com os parâmetros corretos para o escopo escolhido (New Code ou Overall, por projeto ou PR). Persiste em raw-issues.json.
---

# Skill: fetch-codesmells

Consome o `session.json` produzido pela skill `interview-user` e busca os code smells via MCP do SonarQube/SonarCloud. Usa os **tools oficiais** do `sonarqube-mcp-server`.

## Tools do MCP utilizados

Da documentação oficial do `sonarqube-mcp-server` (toolset `issues` + `measures`):

- **`search_sonar_issues_in_projects`** (principal). Parâmetros relevantes:
  - `projects` (array de strings) — chaves dos projetos
  - `impactSoftwareQualities` (array) — usar `["MAINTAINABILITY"]` para filtrar **code smells** na nova taxonomia Clean Code
  - `severities` (array) — `INFO | LOW | MEDIUM | HIGH | BLOCKER`
  - `issueStatuses` (array) — `OPEN | CONFIRMED | FALSE_POSITIVE | ACCEPTED | FIXED | IN_SANDBOX`
  - `pullRequestId` (string, opcional) — para escopo `NEW_CODE` com PR
  - `p` (int) e `ps` (int, max 500) — paginação
- **`get_component_measures`** (suporte para escopo `NEW_CODE` de branch). Parâmetros:
  - `component` — `<projectKey>`
  - `metricKeys` — `["new_violations", "new_maintainability_issues"]` ou similar
  - `pullRequest` (opcional)

## Inputs

- `.sonar-reports/session.json` (gerado pela skill `interview-user`)

## Pré-requisitos

Variáveis de ambiente (já validadas na entrevista, mas re-confirme):
- `SONARQUBE_TOKEN` (obrigatório)
- `SONARQUBE_URL` (default `https://sonarcloud.io`)
- `SONARQUBE_ORG` (obrigatório se URL = SonarCloud)
- `SONARQUBE_TOOLSETS` deve conter pelo menos `issues,projects,measures`

## Passos

### 1. Carregar contrato

Leia `.sonar-reports/session.json`. Extraia:
- `scope` — `OVERALL` ou `NEW_CODE`
- `newcode_subscope` — `PR` ou `BRANCH` (apenas se `NEW_CODE`)
- `project_key`
- `pull_request_id` (apenas se PR)
- `branch` (apenas se branch)
- `severities`
- `impact_software_qualities` (default `["MAINTAINABILITY"]`)
- `issue_statuses` (default `["OPEN", "CONFIRMED"]`)
- `max_issues`

### 2. Construir os parâmetros do MCP

Monte o payload base para `search_sonar_issues_in_projects`:

```json
{
  "projects": ["<project_key>"],
  "impactSoftwareQualities": ["MAINTAINABILITY"],
  "severities": ["MEDIUM", "HIGH", "BLOCKER"],
  "issueStatuses": ["OPEN", "CONFIRMED"],
  "p": 1,
  "ps": 500
}
```

Adicione conforme o escopo:

| Escopo                              | Acrescentar                                                  |
| ----------------------------------- | ------------------------------------------------------------ |
| `OVERALL`                           | nada                                                         |
| `NEW_CODE` + sub-escopo `PR`        | `"pullRequestId": "<pull_request_id>"`                       |
| `NEW_CODE` + sub-escopo `BRANCH`    | nada no payload do MCP — filtragem por new code é manual (ver passo 4) |

### 3. Chamar o MCP e paginar

Invoque `search_sonar_issues_in_projects` com o payload. Itere a paginação (`p = 1, 2, 3, ...`) até:

- Atingir o `max_issues` da sessão, OU
- A página retornar lista vazia / página parcial

Acumule todas as issues em memória.

### 4. Filtro local de "New Code" para escopo BRANCH

Se `scope == "NEW_CODE"` e `newcode_subscope == "BRANCH"`:

a. Chame `get_component_measures` com:
   ```json
   {
     "component": "<project_key>",
     "metricKeys": ["new_violations"]
   }
   ```
   A resposta inclui o `periods` ou `period` com o `date` do início do new code period.

b. Filtre as issues localmente:
   ```
   issues_filtradas = [i for i in issues if i.creationDate >= new_code_period.date]
   ```

c. Se não conseguir obter a data do new code period, avise o usuário e ofereça duas opções:
   - Prosseguir com TODAS as issues do branch (efetivamente Overall com filtro de branch)
   - Cancelar e refazer a entrevista com escopo `OVERALL` ou `NEW_CODE+PR`

### 5. Normalizar o output

Para cada issue retornada pelo MCP, normalize para o schema interno do plugin (compatível com `generate-issue-reports`):

```json
{
  "key": "AY1234abcd",
  "rule": "python:S3776",
  "severity": "HIGH",
  "impact_software_qualities": ["MAINTAINABILITY"],
  "issue_status": "OPEN",
  "component": "my-org_backend:src/api/users.py",
  "file_path": "src/api/users.py",
  "line": 42,
  "message": "Refactor this function to reduce its Cognitive Complexity from 18 to the 15 allowed.",
  "effort": "8min",
  "tags": ["brain-overload"],
  "language": "py",
  "creation_date": "2026-04-30T14:22:11+0000"
}
```

Notas:
- `file_path` é derivado de `component` removendo o prefixo `<projectKey>:`
- `language` vem do campo retornado pelo Sonar; se ausente, infira pela extensão de `file_path`
- Se `component` não tiver o prefixo esperado, use `component` inteiro como `file_path`

### 6. Persistir

Grave em `.sonar-reports/raw-issues.json`:

```json
{
  "session_ref": ".sonar-reports/session.json",
  "fetched_at": "2026-05-13T10:05:00Z",
  "scope": "NEW_CODE",
  "newcode_subscope": "PR",
  "project_key": "my-org_backend",
  "pull_request_id": "142",
  "branch": null,
  "mcp_tool": "search_sonar_issues_in_projects",
  "mcp_params_sent": { /* o payload exato enviado */ },
  "total_returned": 23,
  "total_after_local_filter": 23,
  "issues": [ /* array de issues normalizadas */ ]
}
```

### 7. Resumo ao orquestrador

```
✓ 23 code smells coletados via search_sonar_issues_in_projects
  • Escopo: NEW_CODE / PR 142 do projeto my-org_backend
  • Severidades: 4 HIGH, 15 MEDIUM, 4 LOW
  • Arquivos afetados: 7
  • Linguagens: py (12), ts (8), java (3)
  • Persistido em .sonar-reports/raw-issues.json
```

## Tratamento de erros

| Erro                                              | Ação                                                                  |
| ------------------------------------------------- | --------------------------------------------------------------------- |
| Token ausente / inválido (401, 403)               | Parar, instruir reset do `SONARQUBE_TOKEN`. Nunca logue o token.      |
| projectKey inexistente (404)                      | Sugerir rodar `search_my_sonarqube_projects` para listar              |
| PR não encontrado                                 | Sugerir rodar `list_pull_requests` para confirmar o ID                |
| Sonar retorna 0 issues                            | Avisar: pode ser projeto limpo, escopo errado, ou severidade alta demais. Sugerir baixar a severidade na próxima rodada |
| Rate limit                                        | Recuar com backoff exponencial e avisar                              |
| MCP não responde / `search_sonar_issues_in_projects` indisponível | Conferir `SONARQUBE_TOOLSETS` — deve incluir `issues`     |
| `get_component_measures` indisponível para filtro New Code BRANCH | Cair para o fallback descrito no passo 4c                |
