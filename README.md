# markV AI Plugins

Catálogo de plugins de IA multiplataforma com suporte a **Claude Code**, **GitHub Copilot CLI** e **Cursor**.

Cada plugin é publicado simultaneamente para os três hosts a partir do mesmo repositório, reaproveitando *skills* compartilhadas e disponibilizando agentes adaptados ao formato de cada plataforma.

## Catálogo

| Plugin | Categoria | Descrição | Plataformas |
| --- | --- | --- | --- |
| [`dotnet-unity-tests-plugin`](./dotnet-unity-tests) | testing | Planejador, revisor e criador de testes unitários para .NET (xUnit / MSTest v3). | Claude Code · Copilot CLI · Cursor |
| [`design-docs-plugin`](./design-docs) | documentation | Assistente de entrevista estruturada para gerar PRDs (Geral e Funcional) e HLDs em Markdown, com exportação opcional em JSON. | Claude Code · Copilot CLI · Cursor |
| [`dev-guideline-plugin`](./dev-guideline) | documentation | Gerador de guidelines de desenvolvimento por linguagem, com entrevista guiada e pesquisa em fontes oficiais. | Claude Code · Copilot CLI · Cursor |
| [`plugin-creator-plugin`](./plugin-creator) | development | Assistente de entrevista para criar plugins de IA multiplataforma (Claude Code, Copilot CLI e Cursor). | Claude Code · Copilot CLI · Cursor |

## Plugins

### dotnet-unity-tests-plugin

Automação completa do ciclo de testes unitários em soluções .NET.

- **Agentes:** `dotnet-tester-reviewer` (analisa a solução e gera `test-plan.md`) e `dotnet-tester-creator` (implementa os testes conforme o plano, com meta de 80% de cobertura).
- **Skills:** `dotnet-mstest` (para `net472`) e `dotnet-xunit` (para `net8.0+`).
- **Palavras-chave:** `dotnet`, `unit-tests`, `xunit`, `mstest`, `testing`, `csharp`.
- **Instalação e detalhes:** [`dotnet-unity-tests/README.md`](./dotnet-unity-tests/README.md).

### design-docs-plugin

Entrevista estruturada para geração de documentos técnicos e de produto em Markdown.

- **Agentes:** `design-docs` (orquestrador que pergunta qual tipo de PRD e conduz a entrevista) e `hld-builder` (gerador de HLDs com entrevista estruturada sobre arquitetura, componentes, integração, segurança e escalabilidade).
- **Skills:** `prd-geral` (PRD de alto nível sobre o produto, com enriquecimento opcional via histórico Git), `prd-funcional` (PRD acionável de feature em doze etapas, com exportação opcional em JSON de chaves em inglês) e `new-hld` (HLD descrevendo arquitetura, componentes, fluxos de dados e interfaces, com exportação opcional em JSON).
- **Palavras-chave:** `prd`, `hld`, `product-requirements`, `high-level-design`, `documentation`, `interview`, `product-management`.
- **Instalação e detalhes:** [`design-docs/README.md`](./design-docs/README.md).

### dev-guideline-plugin

Geração de documentos de guidelines de desenvolvimento para uma linguagem específica.

- **Agentes:** `dev-guideline` (entrevista o usuário para mapear a stack do projeto, pesquisa fontes oficiais e gera o documento `<lang>-development-guidelines.md` com 1000-1500 linhas, exemplos de código em stdlib e comandos executáveis).
- **Skills:** `generate-guideline` (entrevista de stack, pesquisa em no mínimo 5 fontes oficiais, template de 26 seções com opcionais por linguagem e regras de validação do documento final).
- **Palavras-chave:** `guidelines`, `development-guidelines`, `coding-standards`, `best-practices`, `style-guide`, `documentation`.
- **Instalação e detalhes:** [`dev-guideline/README.md`](./dev-guideline/README.md).

### plugin-creator-plugin

Assistente para scaffold de novos plugins de IA multiplataforma neste repositório.

- **Agentes:** `plugin-creator` (entrevista nome, agentes, skills e destino; confirma `PLUGIN CONFIGURATION`; gera manifests, agents, copilot-agents, skills, README e entradas de marketplace).
- **Skills:** `create-ai-plugin` (layout obrigatório, templates de manifest por host, diferenças de frontmatter Claude/Cursor vs Copilot, registro em lockstep nos quatro `marketplace.json` e checklist de validação).
- **Palavras-chave:** `plugin`, `plugin-creator`, `scaffold`, `marketplace`, `claude`, `copilot`, `cursor`, `agents`, `skills`.
- **Instalação e detalhes:** [`plugin-creator/README.md`](./plugin-creator/README.md).

## Instalação genérica

Substitua `<plugin-name>` pelo nome do plugin desejado.

```bash
# Claude Code
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install <plugin-name>@markv-ai-plugins

# GitHub Copilot CLI
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install <plugin-name>
```

Para **Cursor**, importe este repositório em *Dashboard → Settings → Plugins → Team Marketplaces → Import*.

## Como contribuir com um novo plugin

1. Siga a estrutura documentada em [`CLAUDE.md`](./CLAUDE.md) (manifests por host, pastas `agents/`, `copilot-agents/`, `skills/`).
2. Acrescente o plugin nos quatro `marketplace.json` do repositório (`./marketplace.json`, `.claude-plugin/`, `.cursor-plugin/`, `.github/plugin/`).
3. Adicione uma linha na tabela **Catálogo** e uma subseção em **Plugins** neste arquivo.

## Autor

Alexandre Danelon (Arquiteto Móvel) — MIT License
