# adrs-management-plugin

Plugin para gestao completa de Architecture Decision Records (ADRs), compativel com **Claude Code**, **GitHub Copilot CLI** e **Cursor**.

O plugin conduz a descoberta e formalizacao da arquitetura do projeto em quatro etapas integradas: Mapeamento modular da base de codigo, Identificacao estruturada de decisoes com scoring e historico git, Geracao formal de documentos no padrao MADR e Vinculacao de relacionamentos bidirecionais clicaveis.

## Fluxo de Uso

### Fase 1: Mapeamento do Codebase (`adr-analyzer` / `adr-map`)

Analisa a estrutura do projeto e gera `docs/adrs/mapping.md`.

- Identifica o stack tecnologico (linguagens, frameworks, bancos de dados, mensageria, cloud).
- Segmenta a base de codigo em modulos logicos e independentes com identificadores claros (ex: `AUTH`, `API`, `DATA`, `PAYMENT`).
- Integra documentos de contexto arquitetural (.md, .txt, diagramas, imagens) se `--context-dir` for informado.

### Fase 2: Identificacao de ADRs Potenciais (`adr-analyzer` / `adr-identify`)

Analisa modulos especificos da base de codigo e gera arquivos de decisoes potenciais em pastas categorizadas por prioridade:

- **Passo 0 (Identificacao Positiva)**: Captura escolhas fundamentais de infraestrutura, plataforma, ORM, APIs e servicos criticos de dominio com pontuacao base garantida (75 pontos).
- **Filtros de Red Flags**: Descarta entidades de negocio puras, fluxos operacionais, configuracoes simples e implementacoes isoladas.
- **Scoring Estrutural (ate 150 pontos)**: Avalia Escopo e Impacto, Custo de Mudanca e Necessidade de Conhecimento pela Equipe. Classifica em `must-document/` (score >= 100) e `consider/` (score 75 a 99).
- **Integracao Git**: Enriquece o contexto com data de introducao e motivacoes de commits.

### Fase 3: Geracao de ADRs Formais (`adr-generator` / `adr-generate`)

Transforma arquivos de ADR potencial em documentos formais no padrao MADR estrito:

- **Estrutura MADR Estrita (7 secoes)**: Context and Problem Statement, Decision Drivers, Considered Options, Decision Outcome, Pros and Cons, Consequences e References.
- **Foco na Decisao**: Zero blocos de codigo no corpo do documento formal (apenas referencias a arquivos com linhas).
- **Classificacao por Tiers**:
  - `generated/{MODULE}/`: Decisoes tecnicas completas.
  - `generated/{MODULE}/needs-input/`: Decisoes com marcadores `[NEEDS INPUT: ...]` para revisao humana de negocio/custos.
- Move o arquivo de ADR potencial processado para `potential-adrs/done/{MODULE}/`.

### Fase 4: Vinculacao e Grafo de Relacionamentos (`adr-linker` / `adr-link`)

Pos-processa o acervo de ADRs gerados e atualiza os cabecalhos dos arquivos:

- **4 Tipos de Relacionamento**: `Supersedes` / `Superseded by`, `Depends on` / `Used by`, `Related to`, `Amends` / `Amended by`.
- **Links Clicaveis em Markdown**: Gera caminhos relativos validos entre modulos.
- **Preservacao de Links Manuais**: Mantem relacionamentos adicionados manualmente e respeita o limite de 3 conexoes por categoria.
- **Emissao de Relatorios**: Salva relatorios detalhados de validacao e matriz de conexoes em `docs/adrs/reports/`.

## Agentes

| Agente | Papel |
| --- | --- |
| `adr-analyzer` | Mapeia o codebase (Fase 1) e identifica ADRs potenciais com scoring e historico git (Fase 2). |
| `adr-generator` | Gera documentos formais no padrao MADR a partir de ADRs potenciais (Fase 3). |
| `adr-linker` | Detecta relacionamentos e gera links bidirecionais clicaveis entre ADRs existentes (Fase 4). |

## Skills

| Skill | Conteudo |
| --- | --- |
| `adr-map` | Procedimento de mapeamento arquitetural modular e geracao de `mapping.md` (disable-model-invocation: true). |
| `adr-identify` | Regras de filtragem (Passo 0 + Red Flags), pontuacao estrutural, integracao git e geracao de ADRs potenciais (disable-model-invocation: true). |
| `adr-generate` | Padrao MADR estrito de 7 secoes, regras de concisao, Tiers de saida e marcadores de lacunas (disable-model-invocation: true). |
| `adr-link` | Deteccao de relacionamentos temporais/tecnicos/semanticos, exclusao de fundacionais e atualizacao atomica de cabecalhos (disable-model-invocation: true). |

## Estrutura de Diretorios do Plugin

```text
adrs-management/
├── .claude-plugin/plugin.json      # Manifest Claude Code
├── .cursor-plugin/plugin.json      # Manifest Cursor
├── plugin.json                     # Manifest Copilot CLI (raiz)
├── agents/                         # Agentes para Claude Code e Cursor (*.md)
│   ├── adr-analyzer.md
│   ├── adr-generator.md
│   └── adr-linker.md
├── copilot-agents/                 # Agentes para Copilot CLI (*.agent.md)
│   ├── adr-analyzer.agent.md
│   ├── adr-generator.agent.md
│   └── adr-linker.agent.md
├── skills/                         # Skills compartilhadas
│   ├── adr-map/SKILL.md
│   ├── adr-identify/SKILL.md
│   ├── adr-generate/SKILL.md
│   └── adr-link/SKILL.md
└── README.md
```

## Estrutura de Artefatos Gerados no Projeto

```text
docs/adrs/
├── mapping.md                           # Fase 1: Mapeamento da arquitetura
├── potential-adrs-index.md              # Fase 2: Indice de decisoes potenciais
├── potential-adrs/                      # Fase 2: Decisoes potenciais
│   ├── must-document/
│   ├── consider/
│   └── done/                            # Arquivamento apos geracao formal
├── generated/                           # Fase 3: ADRs formais no padrao MADR
│   ├── [MODULE-ID]/
│   │   ├── ADR-001-titulo.md
│   │   └── needs-input/
│   │       └── ADR-002-titulo.md
└── reports/                             # Fase 4: Relatorios de conexoes e validacao
    ├── adr-link-report-[timestamp].md
    └── adr-link-validation-[timestamp].md
```

## Instalacao

### Claude Code

```bash
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install adrs-management-plugin@markv-ai-plugins
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install adrs-management-plugin
```

### Cursor

Disponibilize via repositorio de marketplace de time em **Dashboard -> Settings -> Plugins -> Team Marketplaces -> Import**, apontando para o repositorio `markv-ai-plugins`.
