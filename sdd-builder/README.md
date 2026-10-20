# sdd-builder-plugin

Plugin de desenvolvimento orientado a spec (SDD), com fluxo de implementação independente do provedor de LLM. A escolha de modelos se adapta ao harness da sessão: **Codex**, **Claude Code**, **Cursor**, **Antigravity**, **Copilot** ou outro ambiente que carregue as skills e forneça as ferramentas necessárias. Os manifests de distribuição existentes atendem Claude Code, Copilot CLI e Cursor.

Ele conduz o produto do zero até as features implementadas em três etapas encadeadas: PRD com roadmap, specs técnicas por feature e implementação por unidades independentes, com especialistas por tecnologia e plano inicial para escolher modelos de programação e testes por harness. O roadmap `.sdd-builder/prd_map_progress.json` é a fonte única de verdade sobre o progresso e amarra as três etapas.

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

Apresenta o plano de execução e permite escolher os modelos dos especialistas antes de iniciar. Depois das escolhas, implementa a feature fase a fase, com um commit por fase, e atualiza o roadmap ao final.

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

### Plano inicial e escolha de modelos por harness

Antes de alterar código, testes ou roadmap, o `feature-builder` detecta o harness, consulta os modelos disponíveis e apresenta fases, unidades, dependências, especialistas, concorrência e validações. O plano traz duas escolhas independentes:

| Harness detectado | Sugestão para programação | Sugestão para testes |
| --- | --- | --- |
| Codex | GPT-6.1 Sol | GPT-6 Luna |
| Claude Code | Claude Sonnet 5.5 | Claude Haiku 5.5 |
| Cursor | Claude Sonnet 5.5 | Claude Haiku 5.5 |
| Antigravity, Copilot ou outro | Modelo de programação disponível na sessão | Modelo mais leve disponível para testes, quando identificado |

Essas combinações são sugestões do plugin. O catálogo da sessão determina a disponibilidade e os IDs usados no despacho. Os nomes são conferidos nas fontes oficiais de [OpenAI](https://developers.openai.com/api/docs/models), [Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview) e [Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview); isso não garante acesso pela conta ou pelo harness. Para Antigravity, consulte o [catálogo do ambiente](https://www.antigravity.google/docs/models/).

Você pode aceitar as recomendações, herdar o modelo da sessão nos dois papéis ou escolher cada modelo. Se já informou escolhas válidas, o agente apresenta o plano e continua sem perguntar novamente; se informou apenas uma, pergunta pela outra. Sem resposta, a implementação aguarda. Todos os perfis usam herança em vez de um modelo de provedor fixo.

Exemplo de plano no Codex, com os IDs confirmados no catálogo da sessão:

```text
Plano: F03 | Harness: Codex | Execução: parallel | Máximo de workers: 3
Fase 1: contratos em sequência.
Fase 2: implementação e autoria de testes independentes; execução após convergência.
Fase 3: integração, suíte completa e critérios de aceite.
Programação: GPT-6.1 Sol (gpt-6.1-sol), recomendado.
Testes: GPT-6 Luna (gpt-6-luna), recomendado.
Seleção: aguardando escolha do usuário.
```

### Opções da execução

Acrescente as opções ao pedido feito ao `sdd-feature-builder` ou à skill `feature-builder`. São instruções interpretadas pelo agente, não flags de terminal, e valem para a execução atual, inclusive retries e verificação final.

| Opção | Padrão | Uso |
| --- | --- | --- |
| `execution=parallel` | Paralelo elegível | Executa unidades independentes da mesma fase em lotes. |
| `execution=sequential` | Opcional | Mantém um worker por vez, preservando a separação de papéis e contextos. |
| `max-workers=N` | `3` | Limita todos os workers ativos aos slots disponíveis no host. Inteiro positivo. |
| `implementation-model=<ID>` ou `implementation-model=inherit` | Escolha no plano | Modelo de programação para implementação, integração e correções. |
| `test-model=<ID>` ou `test-model=inherit` | Escolha no plano | Modelo para autoria e execução de testes, inclusive validação final. |

Pedido que abre o plano para escolher os modelos:

```text
Implemente F03 com execution=parallel max-workers=3.
```

Escolhas antecipadas no Codex, quando os IDs estiverem disponíveis:

```text
Implemente F03 com implementation-model=gpt-6.1-sol test-model=gpt-6-luna.
```

Escolha por nome no Claude Code/Cursor, resolvida para os IDs do harness:

```text
Implemente F03 com Sonnet 5.5 na programação e Haiku 5.5 nos testes.
```

Herança explícita ou execução sem subagentes:

```text
Implemente F03 com execution=sequential implementation-model=inherit test-model=inherit.
Implemente F03 sem subagentes.
```

A escolha precisa ser aplicada pelo mecanismo real do harness, por chamada ou por perfil existente. Mencionar o modelo no prompt do worker não troca o LLM. A escolha dos especialistas não muda o modelo do orquestrador nem reescreve configurações globais. Sem seleção por worker, o plano informa a limitação e oferece herança, execução inline ou ajuste manual.

Modelo indisponível ou substituição imposta pelo host exige uma alternativa aceita pelo usuário, salvo fallback já autorizado. O relatório informa harness, unidades e modelo solicitado, ID resolvido e modelo efetivo por papel. Quando o host não informa o efetivo, isso fica explícito; não há promessa de economia sem evidência. O contrato completo está em [Seleção de modelos por harness](skills/feature-builder/references/model-selection.md).

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
| `sdd-feature-builder` | Etapa 3. Apresenta plano e escolhas de modelos por harness, coordena unidades, valida, commita e atualiza o roadmap. |
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
| `feature-builder` | Plano inicial, escolha de modelos de programação/testes por harness, unidades independentes, concorrência, commits, verificação final e roadmap. |
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
    │   └── references/
    │       ├── parallel-execution.md
    │       └── model-selection.md
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
