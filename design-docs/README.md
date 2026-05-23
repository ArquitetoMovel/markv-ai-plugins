# design-docs-plugin

Plugin de entrevista estruturada para geração de PRDs (Product Requirements Documents) e HLDs (High-Level Design), compatível com **Claude Code**, **GitHub Copilot CLI** e **Cursor**.

## Fluxo de uso

### Agente `design-docs` — PRDs

O agente **`design-docs`** pergunta ao usuário qual tipo de PRD quer gerar e conduz a entrevista acionando a skill correspondente:

1. **PRD Geral** (skill `prd-geral`): documento de alto nível sobre o produto como um todo. Cobre visão, contexto, público, objetivos, escopo, requisitos macro, estratégia, riscos, KPIs e stakeholders. Quando executado dentro de um repositório Git do próprio produto, pode consultar histórico de commits, issues e fontes para enriquecer o documento.
2. **PRD Funcional** (skill `prd-funcional`): documento acionável sobre uma feature específica. Conduz entrevista em doze etapas cobrindo contexto, problema, objetivos, escopo, requisitos funcionais e não funcionais, arquitetura, decisões, dependências, riscos, critérios de aceitação e testes. Gera o PRD em Markdown e, opcionalmente, também em JSON estruturado com chaves em inglês.

### Agente `hld-builder` — HLDs

O agente **`hld-builder`** conduz uma entrevista estruturada para gerar um HLD (High-Level Design) técnico e acionável usando a skill `new-hld`. O documento descreve:

- Componentes da solução e como se integram
- Fluxos de requisições e dados
- Modelo de dados em alto nível
- Interfaces públicas e contratos
- Considerações de escalabilidade, segurança e observabilidade

Gera o HLD em Markdown e, opcionalmente, também em JSON estruturado.

Ambos os agentes seguem os mesmos princípios de entrevista: uma pergunta por vez, linguagem simples em português, resumo ao final de cada etapa com pedido de confirmação, sem travessões do tipo "—".

## Estrutura de diretórios multiplataforma

```text
design-docs/
├── .claude-plugin/plugin.json     # Manifest Claude Code
├── .cursor-plugin/plugin.json     # Manifest Cursor
├── plugin.json                    # Manifest Copilot CLI (raiz)
├── agents/                        # Agentes para Claude Code e Cursor (*.md)
│   ├── design-docs.md
│   └── hld-builder.md
├── copilot-agents/                # Agentes para Copilot CLI (*.agent.md)
│   ├── design-docs.agent.md
│   └── hld-builder.agent.md
└── skills/                        # Skills compartilhadas entre as 3 plataformas
    ├── prd-geral/SKILL.md
    ├── prd-funcional/SKILL.md
    └── new-hld/SKILL.md
```

## Instalação

### Claude Code

```bash
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install design-docs-plugin@markv-ai-plugins
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install design-docs-plugin
```

### Cursor

Disponibilize via repositório de marketplace de time em **Dashboard → Settings → Plugins → Team Marketplaces → Import**, apontando para o repositório `markv-ai-plugins`.
