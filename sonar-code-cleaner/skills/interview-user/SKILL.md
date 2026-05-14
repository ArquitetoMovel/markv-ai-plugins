---
name: interview-user
description: Entrevista guiada para configurar a sessão de limpeza. Captura escopo (New Code vs Overall) e alvo (projectKey ou PR), usando os tools do MCP do Sonar (search_my_sonarqube_projects, list_pull_requests) para ajudar o usuário quando ele não souber os identificadores.
---

# Skill: interview-user

Conduz uma entrevista **guiada e progressiva** para configurar a sessão de limpeza de code smells. Cada pergunta vem com opções claras e, sempre que possível, **busca informações no Sonar via MCP** para evitar que o usuário tenha que digitar IDs sem contexto.

## Princípios da entrevista

1. **Uma pergunta por vez.** Não bombardear com 5 perguntas no mesmo turno.
2. **Opções > digitação.** Sempre que possível, dar opções `[a]`, `[b]`, `[c]`.
3. **MCP > usuário.** Se o Sonar pode listar projetos/PRs, liste antes de pedir um ID.
4. **Defaults sensatos.** Cada pergunta tem default razoável — usuário pode só apertar Enter.
5. **Confirmação no final.** Antes de chamar o Sonar de verdade, mostre o resumo e peça "OK?".
6. **Persistência.** Toda escolha é gravada em `.sonar-reports/session.json` para auditoria e re-execução.

## Pré-checagem (silenciosa)

Antes da primeira pergunta:

```bash
test -n "$SONARQUBE_TOKEN" || echo "FALTA SONARQUBE_TOKEN"
test -n "$SONARQUBE_URL"   || echo "FALTA SONARQUBE_URL"
# Se SONARQUBE_URL aponta para sonarcloud.io, SONARQUBE_ORG é obrigatório
if echo "$SONARQUBE_URL" | grep -q "sonarcloud.io"; then
  test -n "$SONARQUBE_ORG" || echo "FALTA SONARQUBE_ORG"
fi
```

Se faltar variável, pare e oriente a configurar antes de seguir.

## Fluxo da entrevista

### Pergunta 1 — Escopo das issues

```
Qual escopo de code smells você quer limpar?

  [a] Overall    — todas as issues abertas do projeto (default)
  [b] New Code   — apenas issues introduzidas recentemente
                   (no New Code period do branch ou em um PR específico)

Sua escolha [a/b] (default: a):
```

Mapear:
- `a` → `scope = "OVERALL"`
- `b` → `scope = "NEW_CODE"`

### Pergunta 2 — Alvo (varia conforme o escopo)

**Se `scope = "OVERALL"`:**

```
Para escopo Overall, preciso do projectKey no Sonar.

  [1] Já sei o projectKey, vou digitar
  [2] Não sei — liste os projetos que tenho acesso

Sua escolha [1/2]:
```

- Se `[1]`: pergunte: `Digite o projectKey:` e capture.
- Se `[2]`: chame o tool MCP `search_my_sonarqube_projects` (parâmetro: `page=1`) e mostre os resultados em uma tabela numerada:
  ```
  # 1: my-org_backend-api (My Backend API)
  # 2: my-org_frontend  (My Frontend)
  # 3: my-org_workers   (Background Workers)
  ...
  Digite o número do projeto (ou 'n' para próxima página):
  ```
  Capture a escolha → `projectKey`.

**Se `scope = "NEW_CODE"`:**

Sub-pergunta 2.1 — Qual o sub-escopo do New Code?

```
Para New Code, em qual contexto?

  [a] PR específico    — issues introduzidas em um pull request
  [b] New Code period  — issues introduzidas no período de new code do branch
                          (ex: desde a última versão, últimos 30 dias, etc.)

Sua escolha [a/b]:
```

**Se `[a]` (PR específico):**

Sub-pergunta 2.2 — projectKey (mesmo fluxo da Overall):
- `[1]` digitar diretamente, ou
- `[2]` listar via `search_my_sonarqube_projects`

Sub-pergunta 2.3 — pullRequestId:
```
Você tem o ID do PR no Sonar?

  [1] Sim, vou digitar
  [2] Não — liste os PRs do projeto

Sua escolha [1/2]:
```

- Se `[1]`: capture `pullRequestId` (string).
- Se `[2]`: chame o tool MCP `list_pull_requests` com `projectKey = <capturado>`. Mostre:
  ```
  # 1: PR-142  | feat: add new authentication flow      | branch: feature/auth
  # 2: PR-138  | fix: handle null in user payload       | branch: bugfix/null-user
  ...
  Digite o número do PR:
  ```
  Capture → `pullRequestId`.

**Se `[b]` (New Code period do branch):**

Sub-pergunta 2.2 — projectKey (mesmo fluxo).

Sub-pergunta 2.3 — branch:
```
Qual branch analisar?

  Default (branch git atual): <output de `git rev-parse --abbrev-ref HEAD`>
  Pressione Enter para usar, ou digite outro nome:
```

> ⚠️ Nota técnica: o tool `search_sonar_issues_in_projects` não tem um filtro explícito `sinceLeakPeriod` para issues (esse filtro só existe em `search_security_hotspots`). Para escopo `NEW_CODE` no branch, a estratégia é:
>
> 1. Buscar `new_code_period_baseline_date` via `get_component_measures` com `metricKeys: ["new_development_cost", "new_violations"]` para descobrir a data de corte
> 2. Buscar todas as issues do branch via `search_sonar_issues_in_projects`
> 3. Filtrar localmente pelo campo `creationDate >= baseline_date` antes de gerar relatórios
>
> Documente isso para o usuário se ele perguntar, mas é detalhe da fase 1.

### Pergunta 3 — Severidade mínima

```
Severidade mínima das issues (taxonomia Clean Code do Sonar):

  [a] INFO     — tudo, inclusive observações
  [b] LOW      — baixa e acima
  [c] MEDIUM   — média e acima (default, recomendado)
  [d] HIGH     — apenas alta e bloqueador
  [e] BLOCKER  — apenas bloqueador

Sua escolha [a/b/c/d/e] (default: c):
```

Mapear para `severities`:
- `a` → `["INFO", "LOW", "MEDIUM", "HIGH", "BLOCKER"]`
- `b` → `["LOW", "MEDIUM", "HIGH", "BLOCKER"]`
- `c` → `["MEDIUM", "HIGH", "BLOCKER"]`
- `d` → `["HIGH", "BLOCKER"]`
- `e` → `["BLOCKER"]`

### Pergunta 4 — Limite de issues

```
Limite máximo de issues nesta sessão (evita explosão em projetos grandes):

  Default: 50
  Digite outro valor ou pressione Enter:
```

Capture `max_issues` (int).

## Resumo e confirmação

Após todas as perguntas, mostre:

```
─────────────────────────────────────────────────────
Resumo da configuração da sessão:

  Escopo:           NEW_CODE (PR específico)
  Project key:      my-org_backend-api
  Pull request:     PR-142
  Severidade:       MEDIUM, HIGH, BLOCKER
  Limite:           50 issues
  Impactos:         MAINTAINABILITY (code smells)
  Tool MCP a usar:  search_sonar_issues_in_projects

Confirma e prossigo para a Fase 1? [s/n]:
─────────────────────────────────────────────────────
```

Apenas com `s` (ou `sim`, `yes`, `y`), prossiga. Caso contrário, pergunte o que ajustar.

## Persistência

Grave em `.sonar-reports/session.json`:

```json
{
  "created_at": "2026-05-13T10:00:00Z",
  "scope": "NEW_CODE",
  "newcode_subscope": "PR",
  "project_key": "my-org_backend-api",
  "pull_request_id": "142",
  "branch": null,
  "severities": ["MEDIUM", "HIGH", "BLOCKER"],
  "impact_software_qualities": ["MAINTAINABILITY"],
  "issue_statuses": ["OPEN", "CONFIRMED"],
  "max_issues": 50,
  "mcp_tool": "search_sonar_issues_in_projects"
}
```

Esse arquivo é o **contrato de entrada** da skill `fetch-codesmells`.

## Saída

- Arquivo `.sonar-reports/session.json` em disco
- Confirmação textual ao orquestrador de que a entrevista terminou e está OK

## Tratamento de erros

| Situação                                          | Ação                                                                                    |
| ------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Variáveis de ambiente faltando                    | Parar antes da P1; instruir a configurar                                                |
| Usuário escolhe "listar projetos" mas API retorna vazio | Avisar que o token pode não ter acesso a nenhum projeto                            |
| Usuário escolhe "listar PRs" mas projeto não tem PRs aberto | Oferecer cair para New Code do branch ou Overall                                |
| Usuário cancela na confirmação                    | Perguntar o que ajustar; não chamar Sonar                                              |
| `search_my_sonarqube_projects` ou `list_pull_requests` indisponível | Cair para entrada manual + avisar que o toolset pode não estar habilitado |

## Boas práticas para a entrevista

- **Não revele tokens em log.** Se logar variáveis, mascare `SONARQUBE_TOKEN` com `***`.
- **Não chame `search_sonar_issues_in_projects` durante a entrevista.** Essa chamada é cara — fica para a Fase 1.
- **Cache de listagens.** Se chamar `search_my_sonarqube_projects` e o usuário voltar atrás, reuse o resultado.
- **Aceite atalhos.** Se o usuário escrever de cara "limpe o PR 142 do projeto my-org_backend-api em new code", pule as perguntas correspondentes e vá direto para a confirmação.
