# dev-guideline-plugin

Plugin gerador de guidelines de desenvolvimento por linguagem, compatível com **Claude Code**, **GitHub Copilot CLI** e **Cursor**.

## Fluxo de uso

### Agente `dev-guideline`

O agente **`dev-guideline`** conduz uma entrevista curta para mapear a stack do projeto e gera um documento completo de guidelines usando a skill `generate-guideline`:

1. **Entrevista de stack**: coleta linguagem, ORM, banco de dados, frameworks (principal, web e IA), testes, logging, HTTP client e framework assíncrono. Em projetos com codebase existente, faz um scan do repositório para preencher os parâmetros automaticamente e apenas confirmar com o usuário.
2. **Pesquisa**: consulta no mínimo 5 fontes oficiais (documentação da linguagem, style guides de referência, ferramentas do ecossistema e codebases de produção).
3. **Geração**: produz o documento `<lang>-development-guidelines.md` com 1000-1500 linhas, seções numeradas sequencialmente, mínimo de 20 blocos de código, 5 exemplos "Good vs Bad" e 15 comandos executáveis.

Todos os exemplos de código do documento usam apenas biblioteca padrão ou recursos nativos da linguagem; as bibliotecas da stack aparecem somente na seção "Project Stack", como referência.

## Estrutura de diretórios multiplataforma

```text
dev-guideline/
├── .claude-plugin/plugin.json     # Manifest Claude Code
├── .cursor-plugin/plugin.json     # Manifest Cursor
├── plugin.json                    # Manifest Copilot CLI (raiz)
├── agents/                        # Agente para Claude Code e Cursor (*.md)
│   └── dev-guideline.md
├── copilot-agents/                # Agente para Copilot CLI (*.agent.md)
│   └── dev-guideline.agent.md
└── skills/                        # Skill compartilhada entre as 3 plataformas
    └── generate-guideline/SKILL.md
```

## Instalação

### Claude Code

```bash
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install dev-guideline-plugin@markv-ai-plugins
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install dev-guideline-plugin
```

### Cursor

Disponibilize via repositório de marketplace de time em **Dashboard → Settings → Plugins → Team Marketplaces → Import**, apontando para o repositório `markv-ai-plugins`.
