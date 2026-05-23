---
name: consolidate-results
description: Agrega todos os fix.md gerados pelos especialistas em um SUMMARY.md, lista os arquivos modificados (git diff), e destaca issues que precisam de revisão humana.
---

# Skill: consolidate-results

Última fase do pipeline. Consolida os `REPORT-<NNN>-<slug>.fix.md` produzidos pelos especialistas em um relatório executivo único.

## Inputs

- `.sonar-reports/raw-issues.json` (referência de issues coletadas)
- `.sonar-reports/reports/INDEX.md` (referência de relatórios planejados)
- `.sonar-reports/reports/REPORT-*.fix.md` (resultados dos especialistas)
- Estado atual do `git` (para listar diffs)

## Passos

1. **Listar todos os `.fix.md`** no diretório de relatórios.

2. **Para cada um, extrair:**
   - Nome do especialista
   - Arquivo trabalhado
   - Status (`resolved` / `partial` / `needs-human-review`)
   - Contagem de issues resolvidas vs puladas
   - Observações de risco
   - Validações executadas

3. **Cruzar com o INDEX original** para detectar relatórios sem fix correspondente (`dispatch-failed`).

4. **Coletar diff git:**
   ```bash
   git status --short
   git diff --stat
   ```

5. **Computar métricas agregadas:**
   - Total de issues coletadas
   - Total resolvidas
   - Total puladas (needs-human-review)
   - Total não processadas (dispatch falhou ou relatório sem fix)
   - Distribuição por linguagem / especialista
   - Arquivos modificados

6. **Escrever** `.sonar-reports/SUMMARY.md` com o template abaixo.

## Template do SUMMARY.md

```markdown
# Sonar Code Cleaner — Summary

**Sessão concluída em:** <timestamp ISO>
**Configuração:** [.sonar-reports/session.json](session.json)
**Project key:** <project_key>
**Escopo:** <OVERALL | NEW_CODE/PR-142 | NEW_CODE/BRANCH-main>

## Resultado geral

| Métrica                       | Valor |
| ----------------------------- | ----- |
| Issues coletadas              | 23    |
| Issues resolvidas             | 18    |
| Issues marcadas para revisão  | 4     |
| Issues não processadas        | 1     |
| Relatórios gerados            | 7     |
| Relatórios concluídos         | 7     |
| Arquivos modificados          | 6     |

## Distribuição original por severidade (taxonomia Clean Code)

| Severidade | Coletadas | Resolvidas | Pendentes |
| ---------- | --------- | ---------- | --------- |
| BLOCKER    | 0         | 0          | 0         |
| HIGH       | 4         | 3          | 1         |
| MEDIUM     | 15        | 13         | 2         |
| LOW        | 4         | 2          | 2         |
| INFO       | 0         | 0          | 0         |

## Por especialista

| Especialista          | Relatórios | Issues resolvidas | Issues p/ revisão |
| --------------------- | ---------- | ----------------- | ----------------- |
| @python-expert        | 3          | 10                | 1                 |
| @typescript-expert    | 2          | 6                 | 2                 |
| @java-expert          | 2          | 2                 | 1                 |

## Arquivos modificados (git diff --stat)

```
 src/api/users.py             | 18 +++++++++---------
 src/components/Form.tsx      |  9 +++------
 ...
```

## ⚠️ Requer revisão humana

Os itens abaixo foram marcados pelos especialistas como `needs-human-review`. Cada link
aponta para o `.fix.md` do relatório onde o motivo está detalhado.

1. **src/api/users.py** — `python:S3776` linha 142
   - Motivo: refatoração exigiria mudar contrato público de `authenticate()`
   - Detalhes: [REPORT-001-src__api__users.fix.md](reports/REPORT-001-src__api__users.fix.md)

2. **src/components/Form.tsx** — `typescript:S6478` linha 88
   - Motivo: componente aninhado é usado por testes em outro arquivo
   - Detalhes: [REPORT-002-src__components__Form.fix.md](reports/REPORT-002-src__components__Form.fix.md)

...

## Próximos passos sugeridos

1. **Revise as `needs-human-review`** acima antes de qualquer commit.
2. **Rode os testes do projeto** localmente:
   - `pytest` / `npm test` / `mvn test` / etc.
3. **Faça um commit semântico**, por exemplo:
   ```
   refactor(quality): fix Sonar code smells (closes <N> issues)
   ```
4. **Re-rode a análise do Sonar** (`sonar-scanner` ou via CI) para confirmar redução do débito técnico.
5. **Abra o PR** com link para este `SUMMARY.md` na descrição.
6. **(Opcional) Marcar falsos-positivos no Sonar.** Se algum especialista identificou regra como falso-positivo, você pode pedir ao `@sonar-code-cleaner` para chamar o tool MCP `change_sonar_issue_status` com `status="falsepositive"` — ele sempre vai pedir confirmação antes de fazer isso.

## Não esqueça

- O plugin **não fez commit nem push automaticamente** — todas as mudanças estão apenas no working tree.
- Se algo parecer errado, use `git diff` para inspecionar e `git checkout -- <arquivo>` para reverter parcialmente.
```

## Saída

- Arquivo `.sonar-reports/SUMMARY.md`
- Resumo final impresso ao usuário com link para o arquivo:
  ```
  ✓ Pipeline concluído.
    • 18/23 code smells resolvidos
    • 4 requerem revisão humana
    • 6 arquivos modificados no working tree
    • Detalhes: .sonar-reports/SUMMARY.md
  ```

## Tratamento de erros

| Erro                                | Ação                                                          |
| ----------------------------------- | ------------------------------------------------------------- |
| Nenhum `.fix.md` encontrado         | Avisar que `dispatch-experts` aparentemente não rodou ou falhou |
| Fix reports inconsistentes (sem header esperado) | Incluir no SUMMARY com flag `malformed-report`     |
| `git` indisponível                  | Pular seção de diff e avisar no SUMMARY                       |
