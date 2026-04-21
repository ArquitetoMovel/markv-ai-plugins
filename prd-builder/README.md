# prd-builder-plugin

Plugin de entrevista estruturada para geração de PRDs (Product Requirements Documents), compatível com **Claude Code**, **GitHub Copilot CLI** e **Cursor**.

## Fluxo de uso

O agente de entrada é **`prd-builder`**. Ele pergunta ao usuário qual tipo de PRD quer gerar e conduz a entrevista acionando a skill correspondente:

1. **PRD Geral** (skill `prd-geral`): documento de alto nível sobre o produto como um todo. Cobre visão, contexto, público, objetivos, escopo, requisitos macro, estratégia, riscos, KPIs e stakeholders. Quando executado dentro de um repositório Git do próprio produto, pode consultar histórico de commits, issues e fontes para enriquecer o documento.
2. **PRD Funcional** (skill `prd-funcional`): documento acionável sobre uma feature específica. Conduz entrevista em doze etapas cobrindo contexto, problema, objetivos, escopo, requisitos funcionais e não funcionais, arquitetura, decisões, dependências, riscos, critérios de aceitação e testes. Gera o PRD em Markdown e, opcionalmente, também em JSON estruturado com chaves em inglês.

Ambos os tipos seguem os mesmos princípios de entrevista: uma pergunta por vez, linguagem simples em português, resumo ao final de cada etapa com pedido de confirmação, sem travessões do tipo "—".

## Estrutura de diretórios multiplataforma

```text
prd-builder/
├── .claude-plugin/plugin.json     # Manifest Claude Code
├── .cursor-plugin/plugin.json     # Manifest Cursor
├── plugin.json                    # Manifest Copilot CLI (raiz)
├── agents/                        # Agentes para Claude Code e Cursor (*.md)
│   └── prd-builder.md
├── copilot-agents/                # Agentes para Copilot CLI (*.agent.md)
│   └── prd-builder.agent.md
└── skills/                        # Skills compartilhadas entre as 3 plataformas
    ├── prd-geral/SKILL.md
    └── prd-funcional/SKILL.md
```

## Instalação

### Claude Code

```bash
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install prd-builder-plugin@markv-ai-plugins
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install prd-builder-plugin
```

### Cursor

Disponibilize via repositório de marketplace de time em **Dashboard → Settings → Plugins → Team Marketplaces → Import**, apontando para o repositório `markv-ai-plugins`.
