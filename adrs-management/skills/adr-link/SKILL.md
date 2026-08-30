---
name: adr-link
description: >
  Analisa ADRs existentes, detecta relacionamentos temporais, tecnicos e semanticos (Supersedes, Depends on, Related to, Amends) e atualiza os arquivos com links bidirecionais clicaveis em Markdown.
disable-model-invocation: true
---

# Vinculacao e Grafo de Relacionamentos de ADRs

## Objetivo

Analisar os ADRs formais gerados em `docs/adrs/generated/`, descobrir conexoes arquiteturais entre eles e atualizar os cabecalhos dos arquivos com links bidirecionais clicaveis no padrao Markdown, preservando a integridade das secoes de conteudo.

## Parametros

- `[modules]`: Modulos especificos para processamento (opcional). Se omitido, processa todos os modulos em `{adrs-path}`.
- `--validate`: Modo somente leitura que valida a integridade e reciprocidade dos links existentes sem modificar arquivos.
- `--report-only`: Executa a deteccao e gera o relatorio de relacionamentos sem alterar os arquivos.
- `--adrs-path=<path>`: Diretorio base dos ADRs gerados (padrao: `docs/adrs/generated/`).
- `--output-dir=<path>`: Diretorio para emissao de relatorios (padrao: `docs/adrs/reports/`).

## Tipos de Relacionamento Suportados

### 1. Supersedes / Superseded by
- **Conceito**: Um ADR substitui uma decisao anterior.
- **Criterios**: Sobreposicao semantica de tecnologia/dominio > 50%, diferenca temporal de criacao > 12 meses e evidencias de migracao, refatoracao ou marcadores de depreciacao.
- **Efeito de Status**: O ADR antigo tem seu campo `Status` atualizado para `Superseded`.

### 2. Depends on / Used by
- **Conceito**: Um ADR depende diretamente de outra decisao para funcionar.
- **Criterios**: Mencao explicita a decisao anterior em `Decision Outcome` ou `Context`, utilizacao de contratos/servicos derivados, e data posterior ao ADR base.
- **Exclusao de Fundacionais**: Decisoes de base transversal (como escolha do framework principal, ORM base ou biblioteca de validacao comum) nao devem ser listadas como `Depends on` por todo o sistema para evitar sobrecarga de grafos, exceto se houver extensao direta com confianca > 0.85.

### 3. Related to
- **Conceito**: Decisoes com correlacao tecnica no mesmo dominio sem dependencia estrita.
- **Criterios**: Sobreposicao de palavras-chave entre 50% e 70%, mesmo modulo ou dominios complementares (ex: cobranca e pagamento).

### 4. Amends / Amended by
- **Conceito**: Um ADR faz um ajuste incremental ou extensao pontual a uma decisao previa sem substitui-la por completo.
- **Criterios**: Alta similaridade (> 60%), intervalo temporal curto (< 6 meses) e escopo de refinamento.

## Regras de Formatacao e Limites de Links

1. **Apenas Cabecalhos Modificados**: As 7 secoes de conteudo do MADR nunca devem ser alteradas; apenas os metadados do cabecalho sao atualizados.
2. **Links Clicaveis em Markdown**:
   - Mesmo modulo: `[ADR-005: Titulo](./ADR-005-titulo.md)`
   - Modulo diferente: `[ADR-003: Titulo](../API/ADR-003-titulo.md)`
3. **Limites por ADR**:
   - Maximo de 3 links em `Depends on`.
   - Maximo de 3 links em `Related to`.
   - Sem limite para `Supersedes` e `Amends` (geralmente 0 a 1).
4. **Preservacao de Links Manuais**: Relacionamentos ja definidos manualmente pelo usuario tem prioridade absoluta e sao sempre preservados.

## Exemplo de Cabecalho Atualizado

```markdown
# ADR-015: Redis v6 Cluster Architecture
**Status:** Accepted
**Date:** 2024-08-20
**Supersedes:** [ADR-005: Redis v4 Caching Strategy](./ADR-005-redis-v4-caching.md)
**Depends on:**
- [ADR-003: JWT Authentication](../API/ADR-003-jwt-auth.md)
- [ADR-008: Distributed Rate Limiting](../INFRA/ADR-008-rate-limiting.md)

**Related to:**
- [ADR-012: Session Storage Policy](./ADR-012-session-storage.md)

## Context and Problem Statement
...
```

## Relatorios Gerados

Ao finalizar a execucao, o `adr-linker` emite relatorios detalhados em `{OUTPUT_DIR}/`:
- Relatorio de Relacionamentos: `{output-dir}/adr-link-report-{timestamp}.md`
- Relatorio de Validacao de Links: `{output-dir}/adr-link-validation-{timestamp}.md`
