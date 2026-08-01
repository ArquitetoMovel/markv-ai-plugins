---
name: create-ai-plugin
description: >
  Use esta skill quando o usuário pedir para criar um plugin de IA, scaffold
  de plugin multiplataforma, ou registrar um plugin no marketplace markv-ai-plugins.
  Ativa para "criar plugin", "novo plugin", "plugin-creator", "scaffold plugin",
  "plugin Claude", "plugin Cursor", "plugin Copilot".
---

# create-ai-plugin — Scaffold de plugin de IA multiplataforma

## Objetivo

Conduzir uma entrevista curta e gerar a estrutura completa de um **plugin de IA** compatível com **Claude Code**, **GitHub Copilot CLI** e **Cursor**, seguindo as convenções do repositório `markv-ai-plugins` (specs em `specs/` e guia em `CLAUDE.md`).

O resultado é um diretório instalável com manifests por host, agentes Claude/Cursor e Copilot, skills compartilhadas, README e entradas nos quatro `marketplace.json`.

## Princípios de entrevista

- Faça uma pergunta por vez e aguarde a resposta.
- Não faça perguntas duplas.
- Use português simples e direto (pt-BR).
- Não use travessões do tipo "—".
- Se o usuário não souber, ofereça 2 ou 3 opções plausíveis marcadas como hipótese.
- Ao final de cada bloco, resuma o que entendeu (3 a 6 linhas) e peça confirmação.
- Não invente comportamento do plugin que o usuário não descreveu.

## Perguntas-guia

Colete, nesta ordem:

1. **Nome do plugin** (kebab-case, sem sufixo `-plugin`). Ex.: `code-review`, `api-docs`.
2. **Descrição curta** (uma frase, pt-BR) do que o plugin faz.
3. **Categoria** do marketplace: `testing`, `documentation`, `development`, `productivity`, `security`, `other` (se other, peça o rótulo).
4. **Keywords** (3 a 8 termos em kebab-case ou inglês curto).
5. **Agentes**: quantos e quais nomes; para cada um, descrição em uma frase e papel no fluxo.
6. **Skills**: quantas e quais nomes; para cada uma, o conhecimento canônico que deve conter (o que o agente consulta).
7. **Relação agentes ↔ skills**: qual agente usa qual skill (`<plugin-name>-plugin:<skill-name>`).
8. **Destino**: criar dentro deste repositório `markv-ai-plugins` (padrão) ou apenas gerar o scaffold em outro path?
9. **Versão inicial** (default `1.0.0`) e **autor** (default do marketplace: Alexandre Danelon / alexandre.danelon@outlook.com).
10. **Conteúdo inicial das skills e agentes**: o usuário já tem o texto/prompt, ou o assistente deve redigir um esqueleto com TODOs mínimos a partir da descrição?

Ao final da entrevista, apresente o relatório **PLUGIN CONFIGURATION** e só gere arquivos após confirmação explícita.

### Relatório PLUGIN CONFIGURATION

```text
PLUGIN CONFIGURATION
--------------------
directory:     <plugin-name>/
manifest-name: <plugin-name>-plugin
version:       <version>
category:      <category>
description:   <description>
keywords:      <k1>, <k2>, ...
destination:   markv-ai-plugins | <path>
agents:
  - <agent-name>: <one-line role>
skills:
  - <skill-name>: <one-line purpose>
bindings:
  - <agent-name> -> <plugin-name>-plugin:<skill-name>
author:        <name> <<email>>
```

## Layout obrigatório do plugin

Gere exatamente esta árvore (substitua `<plugin-name>`):

```text
<plugin-name>/
├── .claude-plugin/plugin.json    # Claude Code (sem fields agents/skills)
├── .cursor-plugin/plugin.json    # Cursor (minimal)
├── plugin.json                   # Copilot CLI (agents + skills)
├── agents/                       # Claude + Cursor (*.md)
├── copilot-agents/               # Copilot CLI (*.agent.md)
├── skills/
│   └── <skill-name>/SKILL.md     # compartilhada pelas 3 plataformas
└── README.md
```

Regras:

- Claude Code **auto-escaneia** `agents/` e `skills/`. **Não** coloque campos `agents` ou `skills` em `.claude-plugin/plugin.json` (o validador rejeita `"./agents/"` / `"./skills/"` explícitos).
- Cursor: manifest mínimo em `.cursor-plugin/plugin.json` (sem fields de agents/skills).
- Copilot: `plugin.json` na raiz com `"agents": "copilot-agents/"` e `"skills": ["skills/"]`.
- Corpos dos agentes em pt-BR devem ser **semanticamente idênticos** entre `agents/` e `copilot-agents/`; só o frontmatter muda.
- Skills em `skills/<name>/SKILL.md` são a fonte canônica compartilhada.

## Templates de manifest

### `.claude-plugin/plugin.json`

```json
{
  "name": "<plugin-name>-plugin",
  "description": "<description>",
  "version": "<version>",
  "author": {
    "name": "<author-name>",
    "email": "<author-email>"
  },
  "license": "MIT",
  "repository": "https://github.com/ArquitetoMovel/markv-ai-plugins",
  "keywords": ["<kw1>", "<kw2>"]
}
```

### `.cursor-plugin/plugin.json`

```json
{
  "name": "<plugin-name>-plugin",
  "description": "<description>",
  "version": "<version>",
  "author": {
    "name": "<author-name>",
    "email": "<author-email>"
  },
  "license": "MIT",
  "keywords": ["<kw1>", "<kw2>"]
}
```

### `plugin.json` (Copilot CLI, raiz)

```json
{
  "name": "<plugin-name>-plugin",
  "description": "<description>",
  "version": "<version>",
  "author": {
    "name": "<author-name>",
    "email": "<author-email>"
  },
  "license": "MIT",
  "keywords": ["<kw1>", "<kw2>"],
  "agents": "copilot-agents/",
  "skills": ["skills/"]
}
```

Mantenha `name`, `version`, `description` e `keywords` **idênticos** nos três manifests.

## Frontmatter dos agentes

### Claude / Cursor — `agents/<agent-name>.md`

```markdown
---
name: <agent-name>
description: >
  <descrição ativável em pt-BR, incluindo gatilhos de uso>
model: sonnet
tools:
  - Read
  - Glob
  - Grep
  - Write
  - Bash
skills:
  - <plugin-name>-plugin:<skill-name>
---

# <agent-name>

<corpo do agente em pt-BR>
```

Ajuste a lista `tools` ao que o agente realmente precisa. Inclua só as skills que ele usa.

### Copilot CLI — `copilot-agents/<agent-name>.agent.md`

```markdown
---
name: <agent-name>
description: <mesma descrição em uma linha ou parágrafo curto>
tools: ["bash", "edit", "view"]
---

# <agent-name>

<mesmo corpo em pt-BR do agents/*.md>
```

Diferenças obrigatórias do Copilot:

- Extensão `.agent.md`
- Sem campos `model` e `skills`
- `tools` como array JSON em minúsculas (`bash`, `edit`, `view`, etc.)

## Template de skill — `skills/<skill-name>/SKILL.md`

```markdown
---
name: <skill-name>
description: >
  Quando usar esta skill (gatilhos e escopo). Em português ou inglês curto.
---

# <skill-name>

## Objetivo

<o que a skill ensina o agente a fazer>

## Fluxo / regras

<passos, restrições, formatos de saída>

## Formato de saída (se houver)

<template markdown ou JSON>
```

Coloque o conhecimento canônico na skill; o agente só orquestra e referencia a skill.

## Marketplace (lockstep)

Se o destino for `markv-ai-plugins`, acrescente a **mesma** entrada nos quatro arquivos:

- `marketplace.json` (raiz)
- `.claude-plugin/marketplace.json`
- `.cursor-plugin/marketplace.json`
- `.github/plugin/marketplace.json`

Entrada:

```json
{
  "name": "<plugin-name>-plugin",
  "source": "./<plugin-name>",
  "version": "<version>",
  "description": "<description>",
  "category": "<category>",
  "keywords": ["<kw1>", "<kw2>"]
}
```

Atenção:

- Em `.github/plugin/marketplace.json` o campo top-level `name` do marketplace é `arquiteto-movel-plugins`; nos outros três é `markv-ai-plugins`. **Não altere** o nome do marketplace ao editar; só acrescente o plugin.
- Após adicionar, atualize a tabela **Catálogo** e a seção **Plugins** do `README.md` da raiz do repositório.
- Bumpe `metadata.version` dos marketplaces apenas se o repositório já seguir essa prática na mudança atual; caso contrário, mantenha a versão do marketplace e só registre o plugin.

## README do plugin

Gere `README.md` em pt-BR com:

1. Título e descrição
2. Fluxo de uso (agentes e skills)
3. Árvore de diretórios
4. Instalação Claude Code, Copilot CLI e Cursor (mesmo padrão dos outros plugins)

Exemplo de instalação:

```bash
# Claude Code
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install <plugin-name>-plugin@markv-ai-plugins

# GitHub Copilot CLI
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install <plugin-name>-plugin
```

Cursor: Team Marketplace via Dashboard → Settings → Plugins.

## Checklist de validação (obrigatório antes de declarar pronto)

- [ ] Diretório `<plugin-name>/` criado com os três manifests
- [ ] Claude manifest **sem** fields `agents`/`skills`
- [ ] Copilot aponta `agents` → `copilot-agents/` e `skills` → `["skills/"]`
- [ ] Cada agente existe em `agents/*.md` **e** `copilot-agents/*.agent.md` com corpos alinhados
- [ ] Cada skill tem `skills/<name>/SKILL.md` com frontmatter `name` + `description`
- [ ] Referências de skill no Claude/Cursor usam `<plugin-name>-plugin:<skill-name>`
- [ ] Nomes/versões/descrições/keywords consistentes nos três manifests
- [ ] Quatro `marketplace.json` atualizados em lockstep (se destino = este repo)
- [ ] README do plugin e (se aplicável) README raiz atualizados
- [ ] Conteúdo user-facing em pt-BR
- [ ] Nenhum placeholder TODO/TBD residual se o usuário pediu conteúdo completo; se pediu esqueleto, TODOs devem estar explícitos e mínimos

## Ordem de geração dos arquivos

1. Confirmar PLUGIN CONFIGURATION
2. Criar diretórios
3. Escrever os três manifests
4. Escrever skills
5. Escrever agentes Claude/Cursor e Copilot
6. Escrever README do plugin
7. Atualizar marketplaces + README raiz (se aplicável)
8. Rodar o checklist e reportar o que foi criado

## O que não fazer

- Não gerar arquivos antes da confirmação do relatório PLUGIN CONFIGURATION.
- Não colocar agents/skills dentro de `.claude-plugin/` ou `.cursor-plugin/`.
- Não usar a pasta `agents/` no manifest do Copilot (use `copilot-agents/`).
- Não deixar manifests divergirem entre hosts.
- Não inventar campos de marketplace que o host não usa; copie o estilo das entradas existentes.
- Não criar build, testes ou código de aplicação: este repositório só embarca Markdown e JSON.
