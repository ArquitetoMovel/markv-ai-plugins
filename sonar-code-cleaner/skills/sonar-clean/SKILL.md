---
name: sonar-clean
description: Entry-point. Orquestra ponta-a-ponta a limpeza de code smells do Sonar em 5 fases — entrevista, planos+relatórios segmentados por módulo, correção paralela por especialistas, sumário consolidado e atualização do README do projeto.
---

# /sonar-clean

**Slash command de entrada do plugin `sonar-code-cleaner`.** Quando o usuário digita `/sonar-clean` (com ou sem argumentos), execute o pipeline completo abaixo, na ordem.

Esta skill é a **única coisa** que o usuário precisa lembrar. Tudo o mais (skills internas, agentes especialistas) é invocado por aqui.

## Argumentos opcionais

Aceite atalhos em linguagem natural após o comando para pular perguntas correspondentes da entrevista. Exemplos:

```
/sonar-clean
/sonar-clean PR 142 do projeto my-org_backend
/sonar-clean overall projeto my-org_backend severidade HIGH
/sonar-clean new code do branch main, projeto my-org_backend
/sonar-clean retomar              # se .sonar-reports/session.json existir, pular Fase 1
```

Se os argumentos não cobrirem tudo, a Fase 1 perguntará só o que falta.

## Pré-checagem (silenciosa)

Antes da Fase 1:

```bash
test -n "$SONARQUBE_TOKEN" || echo "FALTA SONARQUBE_TOKEN"
test -n "$SONARQUBE_URL"   || echo "FALTA SONARQUBE_URL"
# Se sonarcloud.io, SONARQUBE_ORG é obrigatório
```

Se faltar, **pare antes da Fase 1** e instrua o usuário (sem expor o valor real).

Se `.sonar-reports/session.json` já existir e o usuário não disse "retomar" explicitamente, pergunte se quer reusar a configuração anterior ou começar do zero.

---

## Fase 1/5 — Entrevista e coleta de contexto

**Skill chamada:** `interview-user`

Anuncie:
```
[1/5] Entrevista e coleta de contexto
```

Invoque a skill `interview-user`, que conduz uma entrevista progressiva (escopo `OVERALL`/`NEW_CODE`, alvo `projectKey`/`pullRequest`, severidade mínima, limite de issues). A skill persiste a configuração em `.sonar-reports/session.json` e exige confirmação final do usuário antes de retornar.

**Saída esperada:** `.sonar-reports/session.json` existe e o usuário confirmou.

**Não prossiga** sem a confirmação.

---

## Fase 2/5 — Geração dos relatórios e plano segmentado

**Skills chamadas:** `fetch-codesmells` + `generate-issue-reports`

Anuncie:
```
[2/5] Coletando issues e gerando plano segmentado por módulos
```

1. Invoque `fetch-codesmells` — ela lê `session.json`, chama o tool MCP `search_sonar_issues_in_projects` com os parâmetros corretos (incluindo `impactSoftwareQualities: ["MAINTAINABILITY"]` para code smells e `pullRequestId` se for escopo PR) e grava `.sonar-reports/raw-issues.json`.

2. Invoque `generate-issue-reports` — ela produz **três níveis** de artefatos:

   - **`.sonar-reports/PLAN.md`** — plano de alto nível agrupado por **módulo** (diretório), listando arquivos afetados, funções/classes tocadas (informativo), distribuição de severidade e ordem sugerida de despacho.
   - **`.sonar-reports/reports/REPORT-<NNN>-<slug>.md`** — **unidade atômica de edição**: um relatório por arquivo. É o que vai para um especialista. A escolha de "1 arquivo = 1 relatório" é deliberada: dois especialistas no mesmo arquivo gerariam conflito de edição, então a segmentação fina (funções) **não** ajuda no paralelismo. A informação de funções vive no PLAN.md como contexto.
   - **`.sonar-reports/reports/INDEX.md`** — tabela linear para a fase de dispatch.

**Resumo a imprimir ao final da Fase 2:**

```
✓ 23 issues coletadas em 3 módulos / 7 arquivos
  • Plano:      .sonar-reports/PLAN.md
  • Relatórios: .sonar-reports/reports/  (7 REPORT-*.md)
  • Índice:     .sonar-reports/reports/INDEX.md
```

---

## Fase 3/5 — Correção em paralelo por especialistas

**Skill chamada:** `dispatch-experts`

Anuncie:
```
[3/5] Despachando especialistas (1 por relatório)
```

### Modo de execução

Apresente ao usuário as **duas opções** de execução logo no início desta fase:

```
Como deseja executar a correção?

  [a] Em série nesta sessão (mais simples, mais lento)
      → Eu vou invocar @python-expert, @typescript-expert, etc. um por um,
        aguardando cada fix.md antes do próximo.

  [b] Em paralelo via multi-sessão (mais rápido para projetos grandes)
      → Você abre N terminais. Eu listo o comando exato para cada relatório.
        Como cada relatório toca um arquivo distinto, não há risco de conflito.
        Quando todos os .fix.md estiverem em disco, retome com /sonar-clean.

Sua escolha [a/b] (default: a):
```

**Se `[a]` (série):**
Invoque `dispatch-experts`, que itera o INDEX.md e despacha o especialista correto para cada relatório, aguardando o `*.fix.md` antes de prosseguir.

**Se `[b]` (paralelo multi-sessão):**
Imprima o conjunto de comandos prontos para colar, um por terminal:

```
# Terminal 1
copilot
> @python-expert resolva .sonar-reports/reports/REPORT-001-src__api__users.md

# Terminal 2
copilot
> @typescript-expert resolva .sonar-reports/reports/REPORT-002-src__components__Form.md

# ... (um por relatório)
```

Diga ao usuário: "Quando todos os `*.fix.md` estiverem em disco, rode `/sonar-clean retomar` para continuar nas Fases 4 e 5."

Verifique a presença dos `*.fix.md` antes de prosseguir — se faltar algum, mostre a lista de pendentes e pause.

---

## Fase 4/5 — Sumário consolidado

**Skill chamada:** `consolidate-results`

Anuncie:
```
[4/5] Consolidando resultados
```

Invoque `consolidate-results`. Ela:
- Agrega todos os `*.fix.md` em `.sonar-reports/SUMMARY.md`
- Lista arquivos modificados via `git status` / `git diff --stat`
- Destaca itens marcados como `needs-human-review`
- Calcula distribuição por severidade (coletadas vs resolvidas vs pendentes)
- Inclui justificativas dos especialistas para issues não corrigidas

**Saída esperada:** `.sonar-reports/SUMMARY.md` existe.

---

## Fase 5/5 — Atualizar o README do projeto

**Skill chamada:** `update-project-readme`

Anuncie:
```
[5/5] Atualizando README do projeto com a seção de Code Quality
```

Invoque `update-project-readme`. Ela:
- Lê `.sonar-reports/SUMMARY.md`
- Encontra o `README.md` na raiz do projeto (ou pergunta onde está)
- Insere/atualiza uma seção marcada entre `<!-- sonar-clean:begin -->` e `<!-- sonar-clean:end -->` com data, contagens, link para o SUMMARY
- **Mostra o diff e pede confirmação explícita antes de salvar**

Se o usuário recusar a alteração do README, registre essa decisão como nota final mas não bloqueie — a sessão de limpeza continua válida.

---

## Mensagem final

Quando todas as fases concluírem, imprima:

```
─────────────────────────────────────────────────────
✓ /sonar-clean concluído.

  • Issues coletadas:  23
  • Issues resolvidas: 18
  • Pendentes humano:  4
  • Arquivos tocados:  6
  • Plano:             .sonar-reports/PLAN.md
  • Sumário:           .sonar-reports/SUMMARY.md
  • README atualizado: README.md (seção sonar-clean)

Próximos passos sugeridos:
  1. Revisar SUMMARY.md (especialmente os "needs-human-review")
  2. Rodar os testes do projeto
  3. Fazer commit (NÃO foi feito automaticamente)
  4. Re-rodar análise do Sonar para confirmar redução do débito
─────────────────────────────────────────────────────
```

## Regras invioláveis

1. **Nunca pular fases.** Cada uma depende dos artefatos da anterior.
2. **Nunca chamar o Sonar antes da confirmação da Fase 1.**
3. **Nunca commitar ou fazer push.** Toda mudança fica no working tree do usuário.
4. **Nunca alterar status de issue no Sonar** (via `change_sonar_issue_status`) sem confirmação explícita do usuário no chat.
5. **Nunca expor tokens em logs.** Se logar variáveis, mascarar `SONARQUBE_TOKEN` com `***`.
6. **Re-executável.** Rodar duas vezes deve ser idempotente — a Fase 1 detecta sessão prévia, a Fase 2 detecta `raw-issues.json`, etc., e oferece reuso ou refresh.

## Quando parar e perguntar

- Variáveis de ambiente faltando → parar antes da Fase 1
- Usuário não confirma a entrevista → não chamar Sonar
- Sonar retorna 0 issues → confirmar configuração antes de prosseguir
- Algum especialista falha repetidamente → marcar como `dispatch-failed` e seguir, sinalizar no SUMMARY
- README do projeto não encontrado → perguntar onde criar/atualizar, ou pular Fase 5 com aviso
