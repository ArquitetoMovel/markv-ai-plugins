# sdd-builder-plugin

Plugin de desenvolvimento orientado a spec (SDD), compatível com **Claude Code**, **GitHub Copilot CLI** e **Cursor**.

Ele conduz o produto do zero até as features implementadas em três etapas encadeadas: PRD com roadmap, specs técnicas por feature e implementação com subagentes especializados por tecnologia. O roadmap `.sdd-builder/prd_map_progress.json` é a fonte única de verdade sobre o progresso e amarra as três etapas.

## Fluxo de uso

### Etapa 1: PRD e roadmap (`sdd-prd-builder`)

Gera `PRD.md` com 9 seções e cria o roadmap de features.

- **Projeto novo**: entrevista completa para extrair objetivo do produto, features principais, benefícios e tecnologias.
- **Projeto existente**: varre `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/`, ADRs, PRDs antigos e o próprio código para extrair o que já existe, e só pergunta o que os arquivos não respondem. Features já implementadas nascem com status `done`. Se o repositório não tiver `AGENTS.md` nem `README.md`, o agente avisa que vale a pena criá-los e registra o aviso no roadmap.

### Etapa 2: specs por feature (`sdd-spec-builder`)

Lê o PRD, seleciona as features em `todo` e gera três documentos por feature em `.sdd-builder/<ID>-<nome-kebab>/`:

- `spec.md`, a especificação técnica de 7 seções
- `plan.md`, o plano de implementação em fases
- `tests.md`, a especificação de casos de teste com rastreabilidade até os critérios de aceite do PRD

Os documentos saem no **mesmo idioma do PRD**, lido do campo `lang` do roadmap. O modo batch gera uma onda inteira em paralelo, com auto-aceite das recomendações, e nunca mistura features de ondas diferentes.

### Etapa 3: implementação (`sdd-feature-builder` e especialistas)

Implementa a feature fase a fase, com um commit por fase, e atualiza o roadmap ao final.

O agente detecta a stack e despacha o especialista correspondente:

| Stack detectada | Especialista |
| --- | --- |
| .NET, C# | `sdd-dotnet-specialist` |
| Python | `sdd-python-specialist` |
| Node, Angular, TypeScript | `sdd-node-angular-specialist` |
| PL/SQL, Oracle | `sdd-plsql-specialist` |
| Java | `sdd-java-specialist` |
| Go | `sdd-go-specialist` |

Passos independentes da mesma fase rodam em paralelo quando tocam arquivos disjuntos. Passos que mexem em manifesto de dependência, injeção de dependência, configuração global, rotas ou migrações nunca são paralelizados.

Ao final, o agente roda a suíte completa, confere o Component Overview arquivo por arquivo, reexecuta os testes que cobrem cada critério de aceite e só marca a feature como `done` se tudo passar.

## Roadmap de progresso

`.sdd-builder/prd_map_progress.json` acompanha cada feature nos status `todo`, `in-progress` e `done`.

```json
{
  "project": "Meu Produto",
  "version": "1.0",
  "lang": "pt-BR",
  "prdPath": ".sdd-builder/PRD.md",
  "updatedAt": "2026-08-01T20:28:00Z",
  "features": [
    { "id": "F01", "name": "Autenticação", "status": "done", "wave": 1, "priority": 1, "specPath": ".sdd-builder/F01-autenticacao/", "updatedAt": "2026-08-01T20:28:00Z", "note": "" }
  ],
  "decisions": [],
  "notes": ""
}
```

Escrita concorrente é evitada por contrato, não por sorte: cada etapa tem um único escritor autorizado, sub-agentes em paralelo nunca escrevem no arquivo, e toda gravação passa por lock de diretório, releitura do disco e troca atômica. As regras completas estão na skill `progress-tracker`.

## Agentes

| Agente | Papel |
| --- | --- |
| `sdd-builder` | Orquestrador. Diagnostica o estado do projeto e roteia para a etapa certa. |
| `sdd-prd-builder` | Etapa 1. PRD de 9 seções e criação do roadmap. |
| `sdd-spec-builder` | Etapa 2. `spec.md`, `plan.md` e `tests.md`, em modo single ou batch por onda. |
| `sdd-feature-builder` | Etapa 3. Implementa, valida, commita por fase e atualiza o roadmap. |
| `sdd-dotnet-specialist` | Implementação .NET e C#. |
| `sdd-python-specialist` | Implementação Python. |
| `sdd-node-angular-specialist` | Implementação Node, Angular e TypeScript. |
| `sdd-plsql-specialist` | Implementação PL/SQL e Oracle. |
| `sdd-java-specialist` | Implementação Java. |
| `sdd-go-specialist` | Implementação Go. |

## Skills

| Skill | Conteúdo |
| --- | --- |
| `prd-builder` | PRD de 9 seções, caminhos greenfield e projeto existente, sistema de IDs de feature, ondas de execução, checklist de validação e criação do roadmap. |
| `spec-builder` | Descoberta de padrões do código em duas camadas, mapeamento PRD para spec, estrutura do `tests.md`, regra de idioma e modo batch por onda. |
| `feature-builder` | Execução por fases, detecção de stack, despacho de especialista, regras de paralelismo, commits, verificação final e atualização do roadmap. |
| `progress-tracker` | Schema do `prd_map_progress.json`, semântica dos status, escritor único por etapa e protocolo de escrita com lock e troca atômica. |

## Estrutura de diretórios multiplataforma

```text
sdd-builder/
├── .claude-plugin/plugin.json      # Manifest Claude Code
├── .cursor-plugin/plugin.json      # Manifest Cursor
├── plugin.json                     # Manifest Copilot CLI (raiz)
├── agents/                         # Agentes para Claude Code e Cursor (*.md)
│   ├── sdd-builder.md
│   ├── sdd-prd-builder.md
│   ├── sdd-spec-builder.md
│   ├── sdd-feature-builder.md
│   ├── sdd-dotnet-specialist.md
│   ├── sdd-python-specialist.md
│   ├── sdd-node-angular-specialist.md
│   ├── sdd-plsql-specialist.md
│   ├── sdd-java-specialist.md
│   └── sdd-go-specialist.md
├── copilot-agents/                 # Agentes para Copilot CLI (*.agent.md)
└── skills/                         # Skills compartilhadas entre as 3 plataformas
    ├── prd-builder/SKILL.md
    ├── spec-builder/
    │   ├── SKILL.md
    │   └── references/feature-template.md
    ├── feature-builder/SKILL.md
    └── progress-tracker/SKILL.md
```

## Artefatos gerados no projeto alvo

```text
.sdd-builder/
├── PRD.md
├── prd_map_progress.json
└── F01-nome-da-feature/
    ├── spec.md
    ├── plan.md
    └── tests.md
```

## Instalação

### Claude Code

```bash
/plugin marketplace add ArquitetoMovel/markv-ai-plugins
/plugin install sdd-builder-plugin@markv-ai-plugins
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add ArquitetoMovel/markv-ai-plugins
copilot plugin install sdd-builder-plugin
```

### Cursor

Disponibilize via repositório de marketplace de time em **Dashboard → Settings → Plugins → Team Marketplaces → Import**, apontando para o repositório `markv-ai-plugins`.
