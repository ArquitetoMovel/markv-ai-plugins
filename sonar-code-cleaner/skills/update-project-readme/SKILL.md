---
name: update-project-readme
description: Atualiza o README.md do projeto com uma seção delimitada por marcadores HTML, refletindo o resultado da última limpeza (de SUMMARY.md). Pede confirmação com diff antes de salvar.
---

# Skill: update-project-readme

Última fase do pipeline `/sonar-clean`. Adiciona ou atualiza uma seção de **Code Quality** no `README.md` do projeto descrevendo a última limpeza realizada — datas, contagens e link para o SUMMARY detalhado.

## Princípios

1. **Idempotência via marcadores.** A seção é delimitada por comentários HTML `<!-- sonar-clean:begin -->` e `<!-- sonar-clean:end -->`. Em execuções subsequentes, substituímos apenas o conteúdo entre os marcadores — nunca duplicamos.
2. **Confirmação obrigatória.** Sempre mostrar o diff e pedir `[s/n]` antes de salvar. O usuário pode recusar e o pipeline continua válido.
3. **Não-invasivo.** Se o README não existe, **não** criar um do zero — perguntar ao usuário (a maioria dos projetos tem README; se não tem, é decisão dele).
4. **Tom factual.** Sem hype, sem "🎉🎉🎉". Tabela com números e link.

## Inputs

- `.sonar-reports/SUMMARY.md` (obrigatório — gerado pela skill `consolidate-results`)
- `.sonar-reports/session.json` (referência adicional — para campos como project_key, escopo)
- `README.md` na raiz do diretório de trabalho (default)

## Passos

### 1. Validar pré-requisitos

```bash
test -f .sonar-reports/SUMMARY.md || echo "FALTA SUMMARY.md — rode /sonar-clean antes"
```

Se faltar, abortar com mensagem orientativa.

### 2. Localizar o README

Procurar por:
- `README.md` (raiz do projeto, default)
- `README.MD`, `Readme.md`, `readme.md` (case-insensitive fallback)
- `docs/README.md` (alguns projetos)

Se não encontrar nenhum:
```
README do projeto não encontrado. O que prefere?
  [a] Criar README.md mínimo com apenas a seção de Code Quality
  [b] Pular esta fase
  [c] Informar caminho alternativo

Sua escolha [a/b/c]:
```

### 3. Extrair métricas do SUMMARY.md

Parsear o SUMMARY.md para pegar:
- Data da sessão
- `project_key`
- Escopo (`OVERALL` / `NEW_CODE/PR-X` / `NEW_CODE/BRANCH-Y`)
- Total coletadas, resolvidas, pendentes (`needs-human-review`), falhas
- Arquivos modificados
- Distribuição por severidade

### 4. Construir o bloco da seção

Use este template (substitua placeholders):

```markdown
<!-- sonar-clean:begin -->
## 🧹 Code Quality

> Última limpeza automatizada via [`sonar-code-cleaner`](https://github.com/SonarSource/sonarqube-mcp-server) plugin do Copilot CLI.

**Sessão:** `<timestamp ISO da última sessão>`
**Escopo:** `<OVERALL | NEW_CODE/PR-142 | NEW_CODE/BRANCH-main>`
**Project key:** `<project_key>`

| Métrica                            | Valor |
| ---------------------------------- | ----- |
| Code smells coletados              | 23    |
| Resolvidos automaticamente         | 18    |
| Pendentes (revisão humana)         | 4     |
| Falhas de despacho                 | 1     |
| Arquivos modificados               | 6     |

### Por severidade (taxonomia Clean Code)

| Severidade | Coletadas | Resolvidas |
| ---------- | --------- | ---------- |
| BLOCKER    | 0         | 0          |
| HIGH       | 4         | 3          |
| MEDIUM     | 15        | 13         |
| LOW        | 4         | 2          |
| INFO       | 0         | 0          |

Relatório completo: [`.sonar-reports/SUMMARY.md`](.sonar-reports/SUMMARY.md)
Plano de execução: [`.sonar-reports/PLAN.md`](.sonar-reports/PLAN.md)

_Esta seção é atualizada automaticamente a cada execução de `/sonar-clean`._
<!-- sonar-clean:end -->
```

### 5. Decidir onde inserir / como atualizar

Lógica:

```python
content = read_file(README)
begin_marker = "<!-- sonar-clean:begin -->"
end_marker   = "<!-- sonar-clean:end -->"

if begin_marker in content and end_marker in content:
    # SUBSTITUIR conteúdo entre marcadores
    new_content = re.sub(
        rf"{begin_marker}.*?{end_marker}",
        new_block,
        content,
        flags=re.DOTALL
    )
elif begin_marker in content or end_marker in content:
    # Marcador órfão — situação inesperada, perguntar ao usuário
    perguntar_o_que_fazer()
else:
    # PRIMEIRA inserção — perguntar onde
    perguntar_onde_inserir()
```

**Se for primeira inserção:**

```
Onde inserir a seção de Code Quality no README?

  [a] No final do arquivo (default, mais seguro)
  [b] Após a primeira seção (logo após o título principal)
  [c] Antes da seção "License" (se existir)
  [d] Não inserir agora — só mostrar o conteúdo para eu copiar manualmente

Sua escolha [a/b/c/d] (default: a):
```

### 6. Mostrar diff e pedir confirmação

**Obrigatório** mostrar o diff antes de salvar, mesmo em substituição. Use:

```bash
diff -u README.md <(echo "$novo_conteudo") | head -60
```

Pergunta:
```
Confirma a alteração no README.md? [s/n]:
```

Só salve com confirmação afirmativa (`s`, `sim`, `yes`, `y`).

### 7. Salvar (se confirmado)

Sobrescreva o `README.md` com `new_content`. Imprima:

```
✓ README.md atualizado (seção sonar-clean).
  Linhas alteradas: +<N> / -<M>
```

Se o usuário recusou (`n`), imprima:
```
README.md não foi alterado. A seção sugerida foi salva em
.sonar-reports/proposed-readme-section.md para você usar manualmente.
```
E grave o bloco proposto em `.sonar-reports/proposed-readme-section.md`.

## Saída

- README.md modificado (com confirmação) **ou** `.sonar-reports/proposed-readme-section.md`
- Mensagem de status ao orquestrador

## Tratamento de erros

| Situação                          | Ação                                                                   |
| --------------------------------- | ---------------------------------------------------------------------- |
| `SUMMARY.md` ausente              | Abortar — rode `/sonar-clean` antes                                    |
| README ausente                    | Menu `[a]/[b]/[c]` descrito acima                                      |
| README é binário / não-UTF8       | Avisar; oferecer gravar bloco em arquivo separado                      |
| Marcadores órfãos (só begin ou só end) | Mostrar contexto, perguntar se deve corrigir ou cancelar          |
| Usuário recusa o diff             | Gravar proposta em `.sonar-reports/proposed-readme-section.md`         |
| Mais de um README candidato encontrado | Listar e pedir escolha                                            |

## Notas

- **Por que marcadores HTML?** Eles são invisíveis no GitHub render mas detectáveis com parser simples. É o padrão usado por ferramentas como `markdown-toc`, `terraform-docs`, etc.
- **Por que não criar README do zero?** Cria risco de sobrescrever um README esperado em CI/CD ou ferramentas de doc. Em projetos sem README, é decisão do usuário criar.
- **Por que pedir confirmação mesmo em substituição?** O README é a vitrine do projeto. Alteração silenciosa quebra confiança.
