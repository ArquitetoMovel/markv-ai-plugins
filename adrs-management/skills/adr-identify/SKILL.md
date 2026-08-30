---
name: adr-identify
description: >
  Identifica decisoes arquiteturais potenciais para modulos especificos com base no mapeamento do codebase (Fase 2). Aplica scoring estrutural, filtros de Red Flags e enriquecimento com historico git.
disable-model-invocation: true
---

# Identificacao de ADRs Potenciais (Fase 2)

## Objetivo

Analisar os modulos do sistema descritos em `mapping.md` para identificar, filtrar e pontuar decisoes arquiteturais relevantes, gerando arquivos de ADRs potenciais com evidencias tecnicas e historico temporal antes da formalizacao.

## Parametros

- `[module-ids]`: Um ou mais IDs de modulos a serem analisados (ex: `AUTH`, `API`, `DATA`).
- `--output-dir=<path>`: Diretorio base de saida (padrao: `docs/adrs`).
- `--adrs-dir=<path>`: Diretorio de ADRs existentes para deteccao de duplicatas e relacoes (padrao: `{OUTPUT_DIR}/generated/`).

## Processo de Identificacao e Filtragem

### Passo 0: Identificacao Positiva (Decisoes Estruturais Fundamentais)

Se a decisao pertencer a uma das categorias abaixo, ela recebe pontuacao base garantida (75/150) e pula diretamente para o scoring:

1. **Servicos de Infraestrutura**: MySQL, PostgreSQL, Redis, RabbitMQ, Kafka, MongoDB, ElasticSearch, AWS/GCP/Azure configs.
2. **Framework ou Plataforma Principal**: Spring Boot, Quarkus, NestJS, Next.js, FastAPI, Django, Symfony, Laravel, ASP.NET Core, Gin.
3. **Camada de Acesso a Dados / ORM**: Prisma, TypeORM, Hibernate, SQLAlchemy, Entity Framework, Doctrine, GORM.
4. **Protocolo ou Estilo de API**: REST, GraphQL, gRPC, WebSocket, SOAP, OpenAPI.
5. **Infraestrutura Critica de Dominio**: Gateways de pagamento, provedores de autenticacao SSO, pipelines de mensageria em tempo real, servicos de IA/ML.

### Passo 1: Filtros de Exclusao (Red Flags)

Para decisoes que nao se enquadram no Passo 0, aplique os seguintes filtros eliminatorios:

- **Red Flag 1: Modelagem de Dominio de Negocio**: Descreve entidades de negocio puras (ex: "Pedido possui Itens"). Apenas estilos arquiteturais de modelagem (ex: "Uso de Value Objects imutaveis") sao aceitos.
- **Red Flag 2: Fluxo de Negocio**: Descreve regras ou processos de negocio operacionais.
- **Red Flag 3: Detalhes de Configuracao Simples**: Parametros isolados sem impacto arquitetural sistemico (ex: `PORT=3000`, `TIMEOUT=30s`).
- **Red Flag 4: Implementacao Trivial / Localizada**: Afeta apenas 1 ou 2 arquivos isolados, substituivel em menos de 2 semanas sem impacto transversal.
- **Red Flag 5: Granularidade Excessiva**: Componente menor de uma decisao maior ja coberta (ex: tempo de expiracao de JWT pertence a estrategia de autenticacao). Deve ser consolidado.

### Regra dos 3 Es
A decisao deve ser:
1. **Estrutural**: Afeta a arquitetura ou integracoes do sistema.
2. **Evidente**: Outros engenheiros precisam entender a razao da escolha.
3. **Estavel**: Durabilidade estimada em meses ou anos, nao semanas.

### Passo 2: Sistema de Pontuacao (Maximo 150 pontos)

- Pontuacao Base: 75 pontos (se Step 0) ou 0 pontos (se analisado via Red Flags).
- **Dimensao 1: Escopo e Impacto (0 a 25 pontos)**:
  - 25: Todo o sistema e integracoes externas.
  - 20: 5+ modulos ou infraestrutura central.
  - 15: 3 a 4 modulos.
  - 10: 1 a 2 modulos.
  - 5: Componente unico.
- **Dimensao 2: Custo de Mudanca (0 a 25 pontos)**:
  - 25: 6+ meses ou inviavel.
  - 20: 2 a 6 meses.
  - 15: 2 a 8 semanas.
  - 10: 1 a 2 semanas.
  - 5: Menos de 1 semana.
- **Dimensao 3: Necessidade de Conhecimento pela Equipe (0 a 25 pontos)**:
  - 25: Todos precisam compreender para trabalhar no projeto.
  - 20: Critico para 80%+ das funcionalidades.
  - 15: Importante para modulos especificos.
  - 10: Ocasionalmente relevante.
  - 5: Raramente necessario.

**Classificacao por Prioridade**:
- **>= 100 pontos**: `must-document/` (Alta Prioridade)
- **75 a 99 pontos**: `consider/` (Media Prioridade)
- **< 75 pontos**: Descartar (Nao documentar)

### Integracao com Historico Git

Para cada decisao pontuada com score >= 75:
- Identificar primeiro commit de introducao (`git log --follow --diff-filter=A`).
- Identificar frequencia de modificacoes e commits com palavras-chave relevantes.
- Enriquecer as secoes do ADR potencial com contexto temporal e de evolucao.

### Contexto com ADRs Existentes

- Comparar palavras-chave com `{ADRS_DIR}`.
- Similaridade > 70%: Alerta de possivel duplicata ou evolucao (`Supersedes`).
- Similaridade 40% a 70%: Decisoes relacionadas (`Related to`).
- Verificar oportunidades de consolidacao.

## Estrutura de Pastas de Saida

```text
{OUTPUT_DIR}/
├── mapping.md
├── potential-adrs-index.md
└── potential-adrs/
    ├── must-document/
    │   └── MODULE-ID/
    │       └── nome-da-decisao-em-kebab-case.md
    └── consider/
        └── MODULE-ID/
            └── nome-da-decisao-em-kebab-case.md
```

## Modelo do Arquivo de ADR Potencial

Nome do arquivo: `nome-da-decisao-em-kebab-case.md` (sem numeros no nome).

```markdown
# Potential ADR: [Titulo Descritivo]

**Module**: [MODULE-ID]
**Category**: [Architecture/Technology/Security/Performance/Infrastructure]
**Priority**: [Must Document (Score: XXX) | Consider (Score: XXX)]
**Date Identified**: [YYYY-MM-DD]

---

## Existing ADR Context
[Anotacoes sobre ADRs existentes similares ou relacionados, se houver]

---

## What Was Identified
[Descricao da decisao identificada com dados temporais do git]

## Why This Might Deserve an ADR
- **Impact**: [Impacto no sistema]
- **Trade-offs**: [Trade-offs visiveis]
- **Complexity**: [Complexidade tecnica]
- **Team Knowledge**: [Necessidade para o time]
- **Future Implications**: [Implicacoes de longo prazo]

## Evidence Found in Codebase
### Key Files
- `caminho/do/arquivo.ext` - Linhas XX-YY

### Code Evidence
[Snippet de codigo ilustrativo]

### Impact Analysis
- Introduced: [Data do git]
- Modified: [X commits ao longo de Y tempo]
- Affects: [X arquivos, Y modulos]

## Questions to Address in ADR (if created)
- Qual problema estava sendo resolvido?
- Por que esta abordagem foi escolhida?
- Quais alternativas foram consideradas?
- Quais sao as consequencias de longo prazo?

## Related Potential ADRs
- [Links para decisoes relacionadas]
```

## Proximos Passos

Apos identificar as decisoes potenciais, utilize a skill `adr-generate` para formalizar os documentos no padrao MADR.
