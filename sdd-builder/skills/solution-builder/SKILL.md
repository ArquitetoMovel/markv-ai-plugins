---
name: solution-builder
description: >
  Inicia, evolui e implementa soluções com múltiplos projetos a partir de um workspace
  que pode não ter Git. Conduz entrevista, elege projeto líder, replica somente artefatos
  da solução em docs/solutions, coordena PRDs locais incrementais, contratos por revisão,
  contextos isolados, ondas, locks Git e validação de integração. Use para solução
  multiprojeto, novo incremento, retomar solução ou coordenar repositórios.
---

# Solution Builder

Coordene uma solução mantendo um PRD e um roadmap por projeto. Esta skill é o contrato
canônico do modo solução nos três hosts. Leia [Contratos persistidos](references/contracts.md)
antes de criar ou retomar artefatos e [Publicação e retomada](references/publication.md)
antes de qualquer escrita global. Não execute o fluxo de um único projeto no diretório
neutro. O workspace não precisa de `.git` nem de `docs/`; apenas os projetos participantes
precisam de checkout Git validado.

## Entrada, descoberta e eleição do líder

1. Aceite descrição livre, caminho do workspace, caminho de um `solution.json`,
   `solutionId`, incremento ou pedido de retomada. Preserve opções já autorizadas,
   incluindo `execution`, `max-workers`, `implementation-model` e `test-model`.
2. Procure `docs/solutions/*/solution.json` no projeto atual. No diretório neutro,
   sonde somente os filhos imediatos (`./*/docs/solutions/*/solution.json`, `./*/.git`,
   inclusive `.git` como arquivo), `./*/docs/PRD.md` e marcadores `pnpm-workspace.yaml`,
   `nx.json`, `go.work`, `*.sln`. Não varra recursivamente repositórios vizinhos.
   Projetos externos e monorepos podem ser informados explicitamente.
3. Agrupe cópias por `solutionId`; cópias da mesma solução não são soluções distintas.
   Se houver mais de uma solução aplicável, peça a seleção. Um diretório neutro sem
   manifesto oferece candidatos e entrevista; nunca invente o catálogo ou objetivo.
4. Confirme a base lógica `WORKSPACE_ROOT`. Resolva e normalize caminhos reais,
   inclusive symlinks, antes de ler/escrever. Verifique em cada projeto
   `git -C <root> rev-parse --show-toplevel` e a identidade do Git comum. `gitRoot` deve
   corresponder à raiz Git real que contém `root`. Detecte checkouts ausentes, destinos
   ignorados pelo Git e colisões entre diretórios de artefatos. Não crie repositório,
   clone, branch ou push como efeito colateral. Greenfield ainda exige Git inicializado
   antes de persistir; peça que o checkout seja preparado se faltar.
5. Respeite o líder indicado. Sem indicação, proponha o menor `projects[].id` em ordem
   lexicográfica entre os checkouts válidos e inclua a escolha no resumo para confirmação.
   Mantenha o líder registrado nas retomadas. Ausência do líder não promove uma réplica.

## Entrevista e inicialização

Com prompt completo, valide os achados e apresente um resumo consolidado antes de
persistir. Sem dados suficientes, pergunte uma coisa por vez e não repita respostas
presentes no prompt ou nos documentos. Colete:

- Objetivo, domínio, requisitos transversais e critérios de aceite de ponta a ponta.
- `solutionId`, catálogo (`id`, nome, `kind=product|platform`, stack, novo/existente),
  `root`, `gitRoot`, `repoUrl` e projeto líder.
- Fronteiras fornecedor/consumidor, tipos de contratos e dependências entre projetos.
- Escopo do incremento inicial `I01`: projetos, entregas e critérios de integração.

Antes de confirmar o catálogo/líder, mantenha respostas na sessão e priorize essa
definição. Depois, registre cada resposta confirmada em
`SOLUTION_DIR/runs/solution-notes.md` e publique nos participantes já confirmados.
Não use arquivos obrigatórios no diretório neutro. Um catálogo parcial pode ter
`links`/`features` vazios até os PRDs locais definirem IDs; não despache SPEC/feature
com referência ainda não resolvida. Inclua novos participantes na próxima publicação.

`SOLUTION_DIR = <leader.root>/docs/solutions/<solution-id>/`.
Cada participante recebe uma cópia em `<project.root>/docs/solutions/<solution-id>/`.
Somente artefatos da solução entram ali. PRDs, roadmaps, features, SPECs, planos,
testes e contratos de feature continuam em `docs/` dos projetos responsáveis.
Checkpoint de PRD: `<project.root>/docs/runs/<run-id>/prd-notes.md`, sem replicação.

## Escritor único e escopo das etapas

O `sdd-solution-builder`, ou `sdd-builder` assumindo este contrato, é o único escritor
de manifesto, snapshots, estado, despacho e réplicas. Não mantenha dois orquestradores
globais ativos. Delegar o entry-point transfere a coordenação; o chamador aguarda.
Os agentes PRD/SPEC/feature recebem `mode=solution` e devolvem mutações propostas;
nem mesmo uma janela sequencial escreve diretamente no roadmap ou em `docs/solutions/`.

O orquestrador valida e aplica essas propostas pelo protocolo de
[progress-tracker](../progress-tracker/SKILL.md), sem mudar seu schema `1.0`:

- PRD: arquivo local com 9 seções e proposta de criação/mesclagem de roadmap.
- SPEC: três documentos locais e proposta apenas de `specPath`.
- Feature: proposta de início e, após verificação, `status`, `note` e `decisions`.
  Marque `in-progress` antes de liberar a primeira escrita de implementação.
- Integração: retorno de evidências; o orquestrador grava as evidências globais e só
  conclui o incremento quando todos os critérios forem comprovados.

Valide caminho e conteúdo no disco, hashes de entrada, IDs, evidências e campos
permitidos; releia sob lock, compare precondições e aplique somente a mudança aceita.
Resultado atrasado/duplicado não é reaplicado. Registre `taskId` e `attempt` em
`state.json`. Uma proposta aceita com publicação incompleta não autoriza dependentes.

## PRDs locais e incrementos

Abra um contexto novo de `sdd-prd-builder` por projeto afetado. O pacote fixa
`PROJECT_ROOT`, `PRD_PATH`, `ROADMAP_PATH` e `PRD_NOTES_PATH`; descoberta de código e
documentação fica nesse projeto. Requisitos transversais chegam por referências
explícitas, não por uma varredura dos demais repositórios.

Na revisão incremental, preserve IDs, `specPath`, estados, decisões e evidências.
IDs novos seguem o maior número já reservado, sem reciclar IDs removidos. Remoções
ficam no roadmap com `note: "no longer in PRD"`, mantendo o status histórico; não
entram no incremento novo. Feature `done` alterada exige reabertura explícita com
impacto aprovado ou nova feature evolutiva. A seção 8 de cada PRD contém só IDs locais;
dependências entre projetos pertencem a `links`. Após validar/mesclar os PRDs, resolva
os IDs globais dos links e do incremento antes de calcular as ondas.

## Grafo e três portões

Identidade global: `projectId:F01`; identidade no projeto: `F01`. Valide unicidade,
existência de projetos/features, direção fornecedor → consumidor e ausência de ciclos
no grafo combinado (dependências locais + links). Referência ausente ou ciclo bloqueia
as tarefas afetadas; nunca relaxe uma dependência para obter um DAG artificial.

Calcule em ordem topológica, não com uma única passagem pela lista de projetos:

```text
onda_solucao(v) = max(onda_interna(v),
                      1 + max(onda_solucao(u) para cada dependência local u),
                      1 + max(onda_solucao(p) para cada provider p nos links))
max(conjunto vazio) = 0
```

Propague o atraso de um fornecedor externo também aos dependentes locais do consumidor.
Use a onda interna da seção 8 como piso. Dentro da onda, ordene por prioridade e ID
global; ondas são uma ordem de liberação, não dispensam os portões:

1. **SPEC/contrato**: a SPEC fornecedora foi gerada, validada e seu contrato registrado
   com `contractRevision`. Consumidor pode ser especificado antes da implementação
   externa, mas não antes do contrato validado. Dependências locais e Foundation
   features não implementadas continuam bloqueando a liberação; Foundations de um
   projeto greenfield são especificadas/implementadas em sequência para estabilizar a base.
2. **Implementação**: dependências locais implementadas; todo provider externo em
   `done`, com evidência verificada, contrato presente e revisão esperada. Verifique
   novamente antes da escrita e em cada barreira de fase. Estado `done` sozinho não basta.
3. **Integração**: todas as features do incremento em `done`, contratos ainda válidos e
   todos os critérios/testes de ponta a ponta aprovados sobre as revisões finais.
   Critério pulado, comando vazio ou ambiente indisponível deixa integração `blocked`,
   nunca `done`. Comando de saída zero sem evidências dos critérios também não basta.

Para features fornecedoras já implementadas sem SPEC, produza/valide o contrato com
revisão documental explicitamente autorizada; não reimplemente nem reabra automaticamente.

## Despacho, isolamento e capacidade do harness

Antes de executar, detecte ferramentas reais de contexto isolado, delegação aninhada,
interação em filhos e seleção nativa de modelos. Registre as capacidades em `state.json`.
Não presuma `Task`, troca de modelo por prompt ou ferramenta de retomada inexistente.

Cada criação/revisão de PRD, SPEC por feature, implementação por feature e validação de
integração usa **contexto novo**, recebendo apenas o caminho do pacote persistido em
`SOLUTION_DIR/runs/<run-id>/dispatch/<project>/<task-id>.json` (use `_solution` para
integração). A instrução de abrir o pacote não inclui o histórico da conversa.
Contexto isolado significa sessão filha sem histórico herdado ou handoff externo novo;
reduzir o prompt em uma sessão que herda o chat inteiro não satisfaz esse contrato.
Repasse preferências e decisões relevantes dentro do pacote.

- Com delegação aninhada: `sdd-feature-builder` coordena workers sob a concessão global.
- Sem delegação aninhada: primeiro despache `feature-plan`, que devolve unidades de
  `work-unit` sem implementar nem alterar status. A sessão principal assume somente a
  coordenação de `feature-builder`, aplica o início, despacha especialistas diretamente,
  converge/valida/commita fase a fase e usa nova janela `feature-review` para verificação
  final e proposta de desfecho. Código e testes continuam em contextos de workers.
- Sem contexto isolado ou com proibição de subagentes: persista pacote e handoff,
  registre `blocked` e instrua nova sessão externa. Nunca execute a tarefa de projeto
  inline no contexto da solução. O fallback inline do modo single-project não se aplica.
- Sem interação em filhos: resolva na sessão principal o plano e os dois seletores de
  `references/model-selection.md` da skill feature-builder; grave solicitado/resolvido
  e fallbacks aceitos. Não escolha pelo usuário nem peça de novo por escolhas válidas.

Modo por onda autoriza `autoAccept` da SPEC apenas quando essa política já foi aceita
no escopo do incremento; cada janela ainda trata uma única feature e registra premissas.
Em entrevista sem interação, devolva perguntas pendentes e checkpoint local, e reabra
outro contexto após as respostas. Não substitua ausência de resposta por consentimento.

## Orçamento global e exclusão Git

`max-workers=3` por padrão limita **todas** as janelas delegadas e workers internos
ativos da solução, inclusive testes; o orquestrador principal não conta. O limite
efetivo é o menor entre o autorizado e a capacidade real. Não dê três slots novos a
cada feature. Reserve capacidade antes do despacho aninhado; não ocupe todos os slots
com coordenadores aguardando filhos. Com apenas um slot, use despacho direto/handoff
em fases, encerrando a janela de planejamento antes do worker.

Projetos com `gitRoot` distintos podem executar em paralelo se recursos e leituras
forem independentes. Etapas mutáveis (PRD, SPEC, implementação, roadmap, publicação e
commits) no mesmo Git são serializadas por concessão exclusiva. O orquestrador reserva
o Git antes de despachar e concede o mesmo token aos workers subordinados; estes não
tentam adquirir de novo o lock que a tarefa já possui. Só unidades disjuntas da mesma
feature/fase podem compartilhar essa concessão. Outra feature/projeto no mesmo Git
aguarda, inclusive monorepo.

Suíte roda com cwd no `PROJECT_ROOT`, usando comandos do projeto; não execute a suíte
do workspace neutro nem de um projeto irmão. Commits usam `git -C <GIT_ROOT>`, na branch
atual, com paths explícitos da fase/projeto. Confira o índice antes de commitar; se
houver stage alheio, não o inclua nem o descarte: bloqueie o commit até isolá-lo.
Não faça `git add .`, `git add -A`, push, reset ou troca de branch. Artefatos de solução
pertencem a publicação/commit separado pelo orquestrador, jamais ao commit da feature.

## Retomada, invalidação e encerramento

1. Reconcilie snapshots e locks conforme a referência de publicação; carregue o estado
   canônico e confira arquivos, commits, entradas e evidências de cada tarefa.
2. Tarefa `running` com sessão/writer ativo não é redisparada. Identificadores nativos
   ficam em metadados locais do lock, não nos snapshots. Sem prova do fim do writer,
   bloqueie; sem API de sessão, use diagnóstico do owner e confirmação de handoff.
3. Mudança no contrato invalida SPEC/feature consumidora ainda não concluída: suspenda
   novos despachos, encerre/aguarde writers afetados, preserve diffs e replaneje com nova
   revisão. Resultado da revisão antiga é rejeitado. Consumidor já `done` exige análise
   de impacto e evolução/reabertura explícita antes de aceitar o novo incremento.
4. Revisão global nova só por progresso de outra tarefa não invalida trabalho válido:
   compare os hashes/contratos e precondições de sua entrada, não só o número da revisão.
5. Em cancelamento/falha, aguarde/encerre workers e comandos antes de liberar locks.
   Preserve alterações e registre tentativas, pendências, último commit e handoff.
6. Validação de integração recebe comandos/cwds/recursos explícitos e revisões dos
   projetos; devolve por critério comando, saída, resultado e evidência. O orquestrador
   persiste o retorno, atualiza o incremento e publica em todos os projetos.

Reporte objetivo, incremento, progresso por projeto, revisão publicada, sincronização,
bloqueios e próximo passo. Não declare conclusão enquanto houver publicação pendente,
feature incompleta, contrato inválido ou integração não comprovada.

## Checklist antes de liberar trabalho

- Líder, workspace e Git de todos os participantes validados; snapshot íntegro e replicado.
- Artefatos globais em `docs/solutions/<solution-id>/`; documentos locais fora dele.
- Grafo sem ciclos/referências ausentes; portões atendidos com revisões verificadas.
- Contexto realmente novo, pacote persistido, modelo e orçamento de slots resolvidos.
- Escritor único, concessão Git e recursos exclusivos atribuídos sem espera circular.
- Retorno validado antes da mutação; nenhuma proposta duplicada, stale ou fora de escopo.
