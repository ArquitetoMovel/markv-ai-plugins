# plugin-creator-plugin

Plugin assistente para criar novos plugins de IA multiplataforma, compatível com **Claude Code**, **GitHub Copilot CLI** e **Cursor**.

## Fluxo de uso

### Agente `plugin-creator`

O agente **`plugin-creator`** conduz uma entrevista curta e gera o scaffold completo usando a skill `create-ai-plugin`:

1. **Entrevista**: coleta nome, descrição, categoria, keywords, agentes, skills, bindings, destino e versão.
2. **Confirmação**: apresenta o relatório `PLUGIN CONFIGURATION` e só gera arquivos após aprovação.
3. **Geração**: cria manifests (Claude, Cursor, Copilot), `agents/`, `copilot-agents/`, `skills/`, README e, quando o destino é este repositório, atualiza os quatro `marketplace.json` e o README raiz.
4. **Validação**: percorre o checklist multiplataforma da skill antes de declarar pronto.

## Estrutura de diretórios multiplataforma

```text
plugin-creator/
├── .claude-plugin/plugin.json     # Manifest Claude Code
├── .cursor-plugin/plugin.json     # Manifest Cursor
├── plugin.json                    # Manifest Copilot CLI (raiz)
├── agents/                        # Agente para Claude Code e Cursor (*.md)
│   └── plugin-creator.md
├── copilot-agents/                # Agente para Copilot CLI (*.agent.md)
│   └── plugin-creator.agent.md
└── skills/                        # Skill compartilhada entre as 3 plataformas
    └── create-ai-plugin/SKILL.md
```

## Instalação

### Claude Code

```bash
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install plugin-creator-plugin@markv-ai-plugins
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install plugin-creator-plugin
```

### Cursor

Disponibilize via repositório de marketplace de time em **Dashboard → Settings → Plugins → Team Marketplaces → Import**, apontando para o repositório `markv-ai-plugins`.
