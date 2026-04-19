# dotnet-unity-tests-plugin

Plugin de planejamento, revisão e criação de testes unitários para .NET, compatível com **Claude Code**, **GitHub Copilot CLI** e **Cursor**.

## Fluxo de uso

O agente de entrada é **`dotnet-tester-coordinator`**. Ele orquestra três fases:

1. **Reviewer** (`dotnet-tester-reviewer`): analisa a solução .NET e gera `test-plan.md` dentro de `<solução>/.dotnet-unity-tests/<session-id>/`
2. **Planner** (`dotnet-tester-planner`): particiona o plano mestre em arquivos `<NomeProjeto>.plan.md` independentes, com metadados de dependência e paralelização no frontmatter
3. **Creator(s)** (`dotnet-tester-creator`): uma instância por `*.plan.md`, disparadas em ondas paralelas respeitando as dependências — cada uma implementa, compila (`dotnet build`), roda (`dotnet test`) e valida cobertura (≥80%) do seu projeto

Todos os artefatos da sessão (plano mestre, planos individuais, resultados, resumo) ficam isolados em `<solução-alvo>/.dotnet-unity-tests/<session-id>/`, permitindo múltiplas execuções coexistirem.

Você também pode invocar `dotnet-tester-reviewer`, `dotnet-tester-planner` ou `dotnet-tester-creator` diretamente se quiser executar apenas uma fase — mas o caminho recomendado é o **coordinator**.

## Estrutura de diretórios multiplataforma

```text
dotnet-unity-tests/
├── .claude-plugin/plugin.json     # Manifest Claude Code
├── .cursor-plugin/plugin.json     # Manifest Cursor
├── plugin.json                    # Manifest Copilot CLI (raiz)
├── agents/                        # Agentes para Claude Code e Cursor (*.md)
│   ├── dotnet-tester-coordinator.md
│   ├── dotnet-tester-creator.md
│   ├── dotnet-tester-planner.md
│   └── dotnet-tester-reviewer.md
├── copilot-agents/                # Agentes para Copilot CLI (*.agent.md)
│   ├── dotnet-tester-coordinator.agent.md
│   ├── dotnet-tester-creator.agent.md
│   ├── dotnet-tester-planner.agent.md
│   └── dotnet-tester-reviewer.agent.md
└── skills/                        # Skills compartilhadas entre as 3 plataformas
    ├── dotnet-mstest/SKILL.md
    └── dotnet-xunit/SKILL.md
```

## Instalação

### Claude Code

```bash
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install dotnet-unity-tests-plugin@arquiteto-movel-plugins
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install dotnet-unity-tests-plugin
```

### Cursor

Disponibilize via repositório de marketplace de time em **Dashboard → Settings → Plugins → Team Marketplaces → Import**, apontando para o repositório `markv-ai-plugins`.
