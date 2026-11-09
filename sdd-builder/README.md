# sdd-builder-plugin

Plugin de desenvolvimento orientado a spec (SDD), com fluxo de implementação independente do provedor de LLM. A escolha de modelos se adapta ao harness da sessão: **Codex**, **Claude Code**, **Cursor**, **Antigravity**, **Copilot** ou outro ambiente que carregue as skills e forneça as ferramentas necessárias. Os manifests de distribuição existentes atendem Claude Code, Copilot CLI e Cursor.

Ele conduz o produto do zero até as features implementadas em três etapas encadeadas: PRD com roadmap, specs técnicas por feature e implementação por unidades independentes, com especialistas por tecnologia e plano inicial para escolher modelos de programação e testes por harness. O roadmap `docs/prd_map_progress.json` é a fonte única de verdade sobre o progresso e amarra as três etapas.

Na versão **1.4.0**, o agente `sdd-solution-builder` adiciona coordenação de múltiplos
projetos, PRDs incrementais, contratos por revisão e integração por incremento. Cada
projeto mantém seu PRD e roadmap; o manifesto da solução conecta esses artefatos.

## Soluções com múltiplos projetos

Inicie `sdd-solution-builder` no diretório neutro do workspace ou peça ao `sdd-builder`
para coordenar uma solução. O workspace **pode não estar versionado em Git**. Somente
os projetos precisam de checkout Git; o plugin não cria `.git` ou exige `docs/` no
diretório neutro.

```text
Inicie uma solução pagamentos neste workspace.
Os projetos são billing em ./api-billing e checkout em ./web-checkout.
Use billing como líder. O incremento I01 deve permitir criar uma fatura pelo checkout
e exibir seu comprovante. Comece pelos requisitos e contratos entre os projetos.
```

Com dados insuficientes, o agente lista candidatos e entrevista uma pergunta por vez.
Ele valida raízes e Git, confirma catálogo/líder e persiste as notas da solução. Sem
líder confirmado, as primeiras respostas ainda ficam na sessão. Sem indicação de líder,
propõe o menor ID de projeto em ordem lexicográfica; a escolha confirmada é estável.

```text
workspace/                                  # Sem Git obrigatório aqui
├── api-billing/                             # Líder, Git próprio
│   └── docs/
│       ├── PRD.md
│       ├── prd_map_progress.json
│       ├── F02-invoices/{spec,plan,tests}.md
│       ├── runs/<run-id>/prd-notes.md
│       └── solutions/pagamentos/            # Fonte canônica da solução
│           ├── SOLUTION.md
│           ├── solution.json
│           ├── snapshot.json
│           └── runs/                        # Notas globais, estado, despacho e integração
└── web-checkout/                            # Git próprio
    └── docs/
        ├── PRD.md
        ├── prd_map_progress.json
        ├── F04-checkout/{spec,plan,tests}.md
        ├── runs/<run-id>/prd-notes.md
        └── solutions/pagamentos/            # Cópia dos artefatos globais do líder
```

**Somente artefatos da solução vão em `docs/solutions/<solution-id>/`**, com cópia em
todos os participantes, inclusive projetos de plataforma. PRDs, roadmaps, features,
SPECs, planos, testes, checkpoints de PRD e contratos definidos nas SPECs continuam no
`docs/` do projeto responsável. Links globais referenciam esses contratos sem copiá-los.
O subdiretório por solução evita colisões quando um projeto participa de várias soluções.

O líder mantém a fonte canônica; o mesmo orquestrador publica as réplicas com revisão
e hashes idênticos. Snapshot incompleto, destino ignorado pelo Git, divergência ou
participante ausente bloqueia novos despachos até reconciliação. Réplicas são de leitura
e não viram líderes automaticamente. Replicar em disco não cria commits nem executa
push. Locks e dados efêmeros de sessão não são replicados/versionados.

O fluxo por incremento é PRD local incremental → SPEC fornecedora → validação do
contrato → SPEC consumidora → implementação na ordem das dependências → integração.
IDs globais usam `billing:F02`; localmente continuam `F02`. A onda da solução combina
dependências internas e links externos e propaga atrasos aos dependentes locais.
Consumidor só é especificado com contrato validado e só é implementado com fornecedores
`done` e verificados. Incremento só termina com os critérios de ponta a ponta aprovados.
Foundation features locais continuam em sequência até estabilizar a base.

Cada PRD, SPEC, implementação e integração recebe um pacote em contexto novo, sem o
histórico completo. Filhos devolvem propostas; o root valida e escreve os roadmaps.
O limite padrão de **3 workers é global**, incluindo janelas e workers internos. Git
distinto permite paralelismo elegível; mesmo `gitRoot` serializa etapas mutáveis e
commits, inclusive em monorepos e durante a publicação das cópias.

Se o host impedir delegação aninhada, a janela de feature planeja unidades e o root
despacha os especialistas diretamente, com verificação final em nova janela. Se não
houver contexto isolado, o plugin registra `blocked` e entrega um handoff para nova
sessão externa. Execução inline no chat da solução não simula isolamento. Sem interação
em filhos, perguntas e escolhas de modelos são resolvidas na sessão principal.

```text
Retome pagamentos a partir de ./web-checkout/docs/solutions/pagamentos/solution.json.
Prepare o incremento I02 preservando IDs, SPECs e evidências das features done.
```

Revisões de PRD preservam histórico; novos IDs não reciclam IDs removidos. Mudança em
feature `done` exige evolução ou reabertura explícita. Na retomada, snapshots, contratos,
locks, tarefas e commits são reconciliados; writer ativo não é redisparado. Caminhos
do manifesto resolvem contra a base do workspace confirmada, inclusive ao partir de
uma réplica. Sem solução selecionada nem pedido multiprojeto, o fluxo local permanece.

Contratos completos: [solution-builder](skills/solution-builder/SKILL.md),
[formatos persistidos](skills/solution-builder/references/contracts.md) e
[publicação/retomada](skills/solution-builder/references/publication.md).
Os [cenários de validação](docs/validation-solution.md) cobrem o fluxo e as falhas esperadas.

## Fluxo de uso

### Etapa 1: PRD e roadmap (`sdd-prd-builder`)

Gera `PRD.md` com 9 seções e cria o roadmap de features.

- **Projeto novo**: entrevista completa para extrair objetivo do produto, features principais, benefícios e tecnologias.
- **Projeto existente**: varre `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/`, ADRs, PRDs antigos e o próprio código para extrair o que já existe, e só pergunta o que os arquivos não respondem. Features já implementadas nascem com status `done`. Se o repositório não tiver `AGENTS.md` nem `README.md`, o agente avisa que vale a pena criá-los e registra o aviso no roadmap.

### Etapa 2: specs por feature (`sdd-spec-builder`)

Lê o PRD, seleciona as features em `todo` e gera três documentos por feature em `docs/<ID>-<nome-kebab>/`:

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
| Codex | GPT-6.1 Sol | GPT-6.1 Terra |
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
Testes: GPT-6.1 Terra (gpt-6.1-terra), recomendado.
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
Implemente F03 com implementation-model=gpt-6.1-sol test-model=gpt-6.1-terra.
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

`docs/prd_map_progress.json` acompanha cada feature nos status `todo`, `in-progress` e `done`.

```json
{
  "project": "Meu Produto",
  "version": "1.0",
  "lang": "pt-BR",
  "prdPath": "docs/PRD.md",
  "updatedAt": "2026-08-01T20:28:00Z",
  "features": [
    { "id": "F01", "name": "Autenticação", "status": "done", "wave": 1, "priority": 1, "specPath": "docs/F01-autenticacao/", "updatedAt": "2026-08-01T20:28:00Z", "note": "" }
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
| `sdd-solution-builder` | Entry-point multiprojeto. Entrevista, líder, replicação, contratos, incrementos e integração. |
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
| `solution-builder` | Workspace sem Git, catálogo/líder, artefatos globais replicados, schemas, pacotes isolados, ondas, locks, propostas e retomada. |
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
│   ├── sdd-solution-builder.md
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
├── docs/validation-solution.md     # Cenários de validação multiprojeto
└── skills/                         # Skills compartilhadas entre as 3 plataformas
    ├── solution-builder/
    │   ├── SKILL.md
    │   └── references/
    │       ├── contracts.md
    │       └── publication.md
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
docs/
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
