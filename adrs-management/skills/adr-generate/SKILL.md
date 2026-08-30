---
name: adr-generate
description: >
  Gera documentos formais de ADR no padrao MADR a partir de arquivos de ADR potencial (Fase 3). Suporta execucao paralela por decisao, numeracao sequencial, deteccao de relacoes e marcadores [NEEDS INPUT].
disable-model-invocation: true
---

# Geracao de ADRs Formais (Fase 3)

## Objetivo

Transformar arquivos de ADRs potenciais (da Fase 2) em documentos formais padronizados no formato MADR com numeracao sequencial, contextualizacao estrategica e marcacao precisa de lacunas para revisao humana.

## Parametros

- `[modules]`: Modulos a serem processados (ex: `AUTH`, `API`, `DATA`).
- `--include-consider`: Inclui decisoes da pasta `consider/` alem de `must-document/`.
- `--context-dir=<path>`: Diretorio com documentos estrategicos adicionais.
- `--language=<code>`: Idioma do documento (padrao: `pt-BR`, `en`, etc.).
- `--output-dir=<path>`: Diretorio base de saida (padrao: `docs/adrs`).

## Principios Fundamentais

1. **Auto-Preenchimento e Lacunas**: Gerar 70% a 80% do conteudo automaticamente a partir das evidencias do codigo e marcar 20% a 30% como `[NEEDS INPUT: ...]` quando envolver fatores de negocio, custos ou regulatorios.
2. **Sem Codigo no Corpo do ADR**: O documento formal de ADR foca na decisao arquitetural, trade-offs e consequencias. Nao incluir blocos de codigo no corpo; utilizar apenas referencias a arquivos com linhas.
3. **Limite de Tamanho**: Cada ADR formal deve ter entre 100 e 250 linhas.
4. **Opcoes Consideradas**: Maximo de 3 opcoes.
5. **Referencias**: Maximo de 3 a 5 arquivos representativos.
6. **Marcadores de Lacuna**: Maximo de 4 marcadores `[NEEDS INPUT: ...]` por ADR.

## Formato MADR Estrito (7 Secoes)

O documento gerado deve conter apenas o cabecalho permitido e exatamente as 7 secoes do MADR:

```markdown
# ADR-XXX: [Titulo da Decisao]

**Status:** Accepted | Proposed | Deprecated | Superseded
**Date:** YYYY-MM-DD
**Related ADRs:** ADR-XXX, ADR-XXX (opcional)

## Context and Problem Statement
[2 a 3 paragrafos contextualizando o cenario e o problema que motivou a decisao]

## Decision Drivers
- [Driver 1: Requisito de escalabilidade, seguranca, padronizacao ou custo]
- [Driver 2: Requisito operacional ou arquitetural]
- [Driver 3: Restricao tecnologica ou de integracao]

## Considered Options
1. [Opcao Escolhida]
2. [Alternativa Principal Considerada]
3. [Outra Alternativa (opcional, maximo 3 opcoes no total)]

## Decision Outcome
Chosen option: "[Nome da Opcao]", because [justificativa tecnica e estrategica principal].

## Pros and Cons of the Options

### [Opcao Escolhida]
- Good, because [vantagem 1]
- Good, because [vantagem 2]
- Bad, because [desvantagem ou custo operacional]

### [Alternativa Considerada]
- Good, because [vantagem]
- Bad, because [motivo da rejeicao]

## Consequences
[2 a 3 paragrafos detalhando impactos positivos, restricoes operacionais e limitacoes decorrentes da escolha]

## References
- `caminho/do/arquivo1.ext:10-35`
- `caminho/do/arquivo2.ext:45-80`
```

## Classificacao em Tiers de Saida

- **Tier 1 (Decisao Completa)**: `{OUTPUT_DIR}/generated/{MODULE}/ADR-XXX-titulo-kebab-case.md`
  - Decisoes puramente tecnicas com evidencias completas e sem lacunas criticas de negocio.
- **Tier 2 (Decisao com Lacunas)**: `{OUTPUT_DIR}/generated/{MODULE}/needs-input/ADR-XXX-titulo-kebab-case.md`
  - Decisoes que dependem de confirmacao de custos, contratos, conformidade regulatoria (LGPD/GDPR) ou direcionamento de negocio.
  - Contem marcadores `[NEEDS INPUT: pergunta especifica]`.

## Arquivamento de Arquivos Processados

Apos a geracao bem-sucedida do ADR formal, o arquivo de ADR potencial correspondente deve ser movido para a pasta de conclusao:
- De: `{OUTPUT_DIR}/potential-adrs/{must-document|consider}/{MODULE}/arquivo.md`
- Para: `{OUTPUT_DIR}/potential-adrs/done/{MODULE}/arquivo.md`

## Proximos Passos

Apos a geracao dos documentos formais, utilize a skill `adr-link` para descobrir dependencias e gerar links bidirecionais entre todos os ADRs gerados.
