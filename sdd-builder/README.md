# sdd-builder-plugin

Plugin de desenvolvimento orientado a spec (SDD), compatível com **Claude Code**, **GitHub Copilot CLI** e **Cursor**.

Ele conduz o produto do zero até as features implementadas em três etapas encadeadas: PRD com roadmap, specs técnicas por feature e implementação por unidades independentes, com especialistas por tecnologia e modelo configurável para testes. O roadmap `.sdd-builder/prd_map_progress.json` é a fonte única de verdade sobre o progresso e amarra as três etapas.

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
| Swift, SwiftUI | `sdd-swift-specialist` |

Cada fase é dividida em unidades com objetivo, arquivos permitidos, dependências e critério de término. Especialistas implementam o código; o `sdd-test-specialist` escreve e executa os testes em unidades separadas. Cada worker recebe apenas os trechos de spec/plano, contratos, casos de teste e convenções necessários ao trabalho, em contexto próprio. Os especialistas carregam a skill curta `work-unit`, sem carregar o fluxo completo do orquestrador.

Unidades da mesma fase rodam em paralelo somente quando não há conflito entre seus arquivos de escrita/leitura nem disputa por banco, build, simulador ou outros recursos. Manifestos, registros DI, configuração global, rotas, migrações, contratos e fixtures compartilhados são ajustados em janelas exclusivas. A autoria de testes pode acompanhar a implementação se depender apenas de contratos estáveis; a execução aguarda o código e os testes prontos.

Depois que todos os writers terminam, o orquestrador confere as alterações e delega a validação conjunta. Ao final da feature, delega a suíte completa, confere o Component Overview e as evidências de cada critério de aceite, e só marca `done` se a verificação passar. Stage, commits e roadmap continuam com um único responsável.

### Escolher modo de execução e modelo de testes

Acrescente as opções ao pedido feito ao `sdd-feature-builder` ou à skill `feature-builder`. Elas são instruções interpretadas pelo agente, não flags de terminal, e valem apenas para a execução atual.

| Opção | Padrão | Uso |
| --- | --- | --- |
| `execution=parallel` | Paralelo elegível | Executa unidades independentes da mesma fase em lotes. |
| `execution=sequential` | Opcional | Mantém um worker por vez, preservando a separação de papéis e contextos. |
| `max-workers=N` | `3` | Limita workers ativos, incluindo testes; respeita também os slots do host. Inteiro positivo. |
| `test-model=inherit` | Modelo herdado | Usa o modelo da sessão que coordena a fase para os workers de testes. |
| `test-model=<ID>` | Opcional | Escolhe um modelo disponível no host para autoria e execução de testes, inclusive validação final. |

Exemplo com um modelo menor no Claude Code, quando o alias `haiku` estiver disponível:

```text
Implemente F03 com execution=parallel max-workers=3 test-model=haiku.
```

Para execução sequencial ou sem subagentes:

```text
Implemente F03 com execution=sequential test-model=inherit.
Implemente F03 sem subagentes.
```

A escolha de modelo dos testes não muda o modelo de implementação. Ela precisa ser aplicada pela ferramenta do host; apenas mencionar o modelo no prompt do worker não o troca. Se o host só aceitar modelo por perfil, a seleção exige um perfil de testes já configurado. O plugin não altera perfis instalados ou configurações globais durante a execução. Consulte os mecanismos de seleção em [Claude Code](https://code.claude.com/docs/en/sub-agents#choose-a-model), [Cursor](https://cursor.com/docs/subagents) e [Copilot CLI](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference).

Sem suporte a seleção por worker ou com modelo indisponível, o fluxo continua com o padrão disponível e informa a preferência não aplicada. Sem concorrência, as unidades rodam em sequência; sem delegação, os papéis são aplicados inline. O relatório informa modo, unidades, limite de workers e modelos solicitado/efetivo; quando o host não informa o modelo efetivo, isso aparece explicitamente. Não há promessa de economia sem confirmação da seleção.

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
| `sdd-feature-builder` | Etapa 3. Decompõe fases, coordena unidades, valida a integração, commita e atualiza o roadmap. |
| `sdd-test-specialist` | Autoria e execução de testes em unidades delimitadas, com modelo selecionável e evidências por TC/AC. |
| `sdd-dotnet-specialist` | Implementação .NET e C#. |
| `sdd-python-specialist` | Implementação Python. |
| `sdd-node-angular-specialist` | Implementação Node, Angular e TypeScript. |
| `sdd-plsql-specialist` | Implementação PL/SQL e Oracle. |
| `sdd-java-specialist` | Implementação Java. |
| `sdd-go-specialist` | Implementação Go. |
| `sdd-swift-specialist` | Implementação Swift e SwiftUI. |

## Skills

| Skill | Conteúdo |
| --- | --- |
| `prd-builder` | PRD de 9 seções, caminhos greenfield e projeto existente, sistema de IDs de feature, ondas de execução, checklist de validação e criação do roadmap. |
| `spec-builder` | Descoberta de padrões do código em duas camadas, mapeamento PRD para spec, estrutura do `tests.md`, regra de idioma e modo batch por onda. |
| `feature-builder` | Execução por fases e unidades independentes, seleção de modelo de testes, limites de concorrência, commits, verificação final e roadmap. |
| `work-unit` | Contrato curto dos workers: papel, contexto mínimo, arquivos, dependências, recursos e retorno com evidências. |
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
│   ├── sdd-test-specialist.md
│   ├── sdd-dotnet-specialist.md
│   ├── sdd-python-specialist.md
│   ├── sdd-node-angular-specialist.md
│   ├── sdd-plsql-specialist.md
│   ├── sdd-java-specialist.md
│   ├── sdd-go-specialist.md
│   └── sdd-swift-specialist.md
├── copilot-agents/                 # Agentes para Copilot CLI (*.agent.md)
└── skills/                         # Skills compartilhadas entre as 3 plataformas
    ├── prd-builder/SKILL.md
    ├── spec-builder/
    │   ├── SKILL.md
    │   └── references/feature-template.md
    ├── feature-builder/
    │   ├── SKILL.md
    │   └── references/parallel-execution.md
    ├── work-unit/SKILL.md
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
