---
name: adr-map
description: >
  Cria um mapeamento modular da arquitetura do codebase para preparar a identificacao de ADRs (Fase 1). Analisa estruturas, tecnologias, modulos e dependencias do sistema.
disable-model-invocation: true
---

# Mapeamento de Arquitetura do Codebase (Fase 1)

## Objetivo

Mapear a estrutura modular da base de codigo para fornecer o contexto necessario a identificacao de decisoes arquiteturais (ADRs) na Fase 2.

## Parametros

- `--project-dir=<path>`: Diretorio do projeto a mapear (padrao: `.` diretorio atual)
- `--context-dir=<path>`: Diretorio com documentos de contexto arquitetural (.md, .txt, diagramas, imagens, PDFs)
- `--output-dir=<path>`: Diretorio base de saida (padrao: `docs/adrs`)

## Fluxo de Execucao

1. **Parse de Argumentos**: Extrair diretorio do projeto, diretorio de contexto e diretorio de saida.
2. **Carregamento de Contexto** (se `--context-dir` for fornecido): Ler documentos arquiteturais, diagramas e especificacoes existentes para identificar padroes declarados e dominios de negocio.
3. **Analise da Estrutura do Projeto**: Mapear pastas, modulos, pontos de entrada e padroes estruturais no `--project-dir`.
4. **Identificacao do Stack Tecnologico**: Detectar linguagens, frameworks principais, bancos de dados, filas de mensagens, caches e servicos em nuvem.
5. **Mapeamento de Modulos**: Dividir o sistema em modulos logicos e independentes com identificadores curtos em maiusculas (ex: `AUTH`, `API`, `DATA`, `PAYMENT`, `INFRA`).
6. **Integracao de Insights**: Comparar a estrutura de codigo descoberta com os documentos de contexto fornecidos, anotando discrepancias e dominios de negocio.
7. **Criacao do Arquivo de Mapeamento**: Gerar `{OUTPUT_DIR}/mapping.md`.

## Estrutura do Arquivo `mapping.md`

```markdown
# Codebase Architecture Mapping

## Project Overview
[Nome, proposito, tipo de aplicacao, linguagens, frameworks principais]

## Technology Stack
[Detalhamento completo do stack tecnologico]

## Context Notes (Opcional: quando --context-dir for fornecido)
**Arquivos de Origem**: [Lista de arquivos analisados]

**Principais Insights**:
- Padroes arquiteturais mencionados: [padroes de docs/diagramas]
- Dominios de negocio identificados: [dominios]
- Limites de modulos documentados: [cruzamento com o codigo]
- Tecnologias documentadas vs encontradas: [comparativo]
- Discrepancias: [diferencas observadas]

## System Modules
[Lista de modulos logicos com identificadores unicos]

### Module Index
1. [MODULE-ID] - [Nome do Modulo]: [Descricao em uma linha]

### [MODULE-ID]: [Nome do Modulo]
**Proposito**: [O que o modulo faz]
**Localizacao**: `caminho/*`
**Componentes Principais**: [Lista de componentes]
**Tecnologias**: [Especificas deste modulo]
**Dependencias**: Internas e externas
**Padroes**: [Padroes arquiteturais aplicados]
**Arquivos Chave**: [Exemplos representativos]
**Escopo**: [Pequeno/Medio/Grande] - [Contagem aproximada de arquivos]

## Cross-Cutting Concerns
[Infraestrutura, Autenticacao, Camada de Dados, Camada de API, Observabilidade, Integracoes]
```

## Proximos Passos

Apos a geracao do `mapping.md`, execute a skill `adr-identify` para identificar as decisoes arquiteturais potenciais nos modulos mapeados.
