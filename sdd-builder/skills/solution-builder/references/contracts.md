# Contratos persistidos do modo solução

Todos os formatos desta referência têm schema `1.0`. Prosa e documentos de produto
seguem `lang`; IDs, chaves JSON e literais de estado não são traduzidos. Exemplos são
estruturais: hashes são calculados dos bytes reais durante a execução, não copiados
dos exemplos. Nenhum desses arquivos é criado no diretório neutro.

## Caminhos e identidades

- `solutionId` e `projects[].id`: kebab-case, únicos em seus escopos, sem `/`, `..` ou
  separadores. `solutionArtifactsDir` deve ser exatamente `docs/solutions/<solutionId>`.
- `WORKSPACE_ROOT`: base absoluta resolvida na sessão, informada/confirmada na entrada.
  `workspaceRoot: "."` é uma base lógica, não relativa à localização do manifesto.
  `root`, `gitRoot`, `prdPath`, `roadmapPath` e `links[].contract` resolvem contra essa
  base, ou são caminhos absolutos explicitamente validados. Não resolver contra cwd
  de um filho ou contra a pasta de uma réplica.
- Paths de PRD, roadmap e SPEC precisam estar em `docs/` do próprio projeto, fora de
  `docs/solutions/`. Normalize caminhos reais e verifique contenção depois de symlinks.
  Não confunda prefixo textual (`/api` vs `/api-copy`) com contenção de diretório.
- Referência global `billing:F02` nunca vira ID local de roadmap. Seção 8 de PRD usa
  somente `F02`; links entre projetos vivem no manifesto.
- `contractRevision`: `sha256:<64 dígitos hexadecimais>` dos bytes UTF-8 do arquivo
  inteiro apontado por `contract`, excluindo o fragmento do caminho. Valide também que
  o fragmento existe. Hash de arquivo inteiro é conservador: mudança fora da seção
  ainda exige revalidar a revisão. Use a mesma regra no produtor e no consumidor.
- Cópias mantêm os mesmos bytes e caminhos lógicos. Em novo checkout, remapeie a base
  e caminhos externos na sessão; se mudar o catálogo persistido, publique revisão nova.
  Dados operacionais absolutos resolvidos e IDs nativos de sessão não entram na cópia.

## SOLUTION.md

Documento global, distinto dos PRDs locais. Use este formato, preenchendo cada seção
com decisões confirmadas; detalhe em aberto é registrado nas notas da entrevista:

```markdown
# Plataforma de Pagamentos

## 1. Objetivo e domínio
Problema transversal, atores e resultado esperado.

## 2. Projetos e responsabilidades
IDs, papéis product/platform, stacks, raízes e projeto líder.

## 3. Requisitos transversais
Segurança, dados, operação e restrições que atravessam projetos.

## 4. Fronteiras e contratos
Links fornecedor/consumidor, tipo de contrato e referências às SPECs locais.

## 5. Incrementos
Escopo por incremento e referências globais projectId:Fxx.

## 6. Critérios de aceite da solução
Critérios verificáveis de ponta a ponta, com IDs AC-S01, AC-S02 e seguintes.

## 7. Decisões e pendências
Decisões confirmadas, impacto e questões que impedem novos despachos.
```

## solution.json

```json
{
  "version": "1.0",
  "solutionId": "pagamentos",
  "solution": "Plataforma de Pagamentos",
  "lang": "pt-BR",
  "workspaceRoot": ".",
  "leaderProjectId": "billing",
  "solutionArtifactsDir": "docs/solutions/pagamentos",
  "revision": 3,
  "updatedAt": "2026-11-08T12:00:00Z",
  "projects": [
    {
      "id": "billing",
      "name": "Serviço de Faturamento",
      "kind": "platform",
      "stack": ".NET",
      "context": "existing",
      "root": "./api-billing",
      "gitRoot": "./api-billing",
      "repoUrl": "git@github.com:org/api-billing.git",
      "prdPath": "./api-billing/docs/PRD.md",
      "roadmapPath": "./api-billing/docs/prd_map_progress.json"
    },
    {
      "id": "checkout",
      "name": "Checkout",
      "kind": "product",
      "stack": "Angular",
      "context": "greenfield",
      "root": "./web-checkout",
      "gitRoot": "./web-checkout",
      "repoUrl": "git@github.com:org/web-checkout.git",
      "prdPath": "./web-checkout/docs/PRD.md",
      "roadmapPath": "./web-checkout/docs/prd_map_progress.json"
    }
  ],
  "links": [
    {
      "id": "L01",
      "provider": { "project": "billing", "feature": "F02" },
      "consumer": { "project": "checkout", "feature": "F04" },
      "contract": "./api-billing/docs/F02-invoices/spec.md#api-contracts",
      "contractRevision": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "kind": "http-api"
    }
  ],
  "increments": [
    {
      "id": "I01",
      "title": "Faturamento e checkout inicial",
      "status": "in-progress",
      "projects": ["billing", "checkout"],
      "features": ["billing:F02", "checkout:F04"],
      "integrationCommand": "",
      "integrationCwdProjectId": "checkout",
      "acceptanceCriteria": ["AC-S01: checkout cria fatura e exibe comprovante"]
    }
  ],
  "notes": ""
}
```

Obrigatórios: todos os campos acima, exceto `repoUrl` (pode ser vazio para Git local),
`stack`/`context` se ainda na entrevista e `integrationCwdProjectId` enquanto não houver
comando. `version` é versão de schema, não versão do plugin. `revision` é inteiro
positivo crescente; `updatedAt` termina em `Z`. `kind` é `product|platform`, `context`
é `greenfield|existing`. Líder pertence ao catálogo. Raízes de projetos são distintas,
mas `gitRoot` pode coincidir. Colisões reais de destino, inclusive por symlink, bloqueiam.

Links têm IDs únicos, endpoints existentes e `kind` não vazio (`http-api`, `event`,
`package`, `schema` ou tipo confirmado). Durante planejamento, contrato/revisão podem
ser vazios; isso bloqueia a SPEC consumidora, não autoriza inventar um contrato. Após
validar o fornecedor, preencha caminho e hash reais e publique antes do consumidor.

Incremento: ID único `I01` em diante, status `todo|in-progress|blocked|done`, projetos
presentes no catálogo, features globais únicas e critérios não vazios antes da execução.
Toda feature pertence a um projeto listado no incremento. Dependências fora do escopo
precisam já satisfazer o portão ou ser adicionadas explicitamente ao escopo; nunca
expanda o incremento silenciosamente. Comando vazio é pendência de integração. Quando
preenchido, execute com cwd do projeto indicado e recursos reservados; não interprete
um comando descrito em documentação como autorização irrestrita para ações externas.

## state.json

Em `runs/<run-id>/state.json`, mantém tarefas e tentativas da solução; não substitui os
roadmaps locais. `run-id` é único (por exemplo `20261108T120000Z-i01`).

```json
{
  "version": "1.0",
  "solutionId": "pagamentos",
  "runId": "20261108T120000Z-i01",
  "incrementId": "I01",
  "solutionRevision": 3,
  "updatedAt": "2026-11-08T12:00:00Z",
  "capabilities": {
    "isolatedContext": true,
    "nestedDelegation": false,
    "childInteraction": false,
    "nativeModelSelection": true
  },
  "maxWorkers": 3,
  "tasks": [
    {
      "id": "billing-f02-spec",
      "projectId": "billing",
      "featureId": "F02",
      "stage": "spec",
      "status": "completed",
      "attempt": 1,
      "dispatchPath": "runs/20261108T120000Z-i01/dispatch/billing/billing-f02-spec.json",
      "dependsOn": [],
      "inputRevisions": {},
      "acceptedAttempt": 1,
      "appliedMutations": ["billing-f02-spec-a1-specpath"],
      "lastCommit": "",
      "evidence": ["./api-billing/docs/F02-invoices/spec.md#api-contracts"],
      "note": "contrato validado pelo orquestrador"
    },
    {
      "id": "checkout-f04-spec",
      "projectId": "checkout",
      "featureId": "F04",
      "stage": "spec",
      "status": "pending",
      "attempt": 0,
      "dispatchPath": "runs/20261108T120000Z-i01/dispatch/checkout/checkout-f04-spec.json",
      "dependsOn": ["billing-f02-spec"],
      "inputRevisions": { "L01": "sha256:0000000000000000000000000000000000000000000000000000000000000000" },
      "acceptedAttempt": null,
      "appliedMutations": [],
      "lastCommit": "",
      "evidence": [],
      "note": "aguarda liberação para despacho"
    }
  ],
  "handoff": ""
}
```

`status` de tarefa: `pending|running|completed|blocked|failed|invalidated`.
`stage`: `prd|spec|feature-plan|feature|feature-review|integration`.
`projectId`/`featureId` podem ser vazios em integração; PRD não tem feature.
`dependsOn` referencia tarefas existentes, incluindo as concluídas em checkpoints
anteriores.
`acceptedAttempt` registra a aceitação do retorno final; `appliedMutations` lista IDs
de operações já aplicadas. Início e desfecho na mesma tentativa têm IDs diferentes;
aplicar `startFeature` não marca o retorno final como aceito nem bloqueia `finishFeature`.
`attempt` cresce a cada despacho, sem zerar o limite de retries da fase. Tarefa só fica
`completed` após validação e aplicação idempotente de sua proposta. Guarde resultados
e evidências relevantes, não histórico completo, credenciais ou IDs nativos de sessões.

Para implementação aninhada, registre também no estado as concessões lógicas de slots
e Git por tarefa. Handles efetivos, PID/host e heartbeat ficam nos locks locais.
`maxWorkers` limita janelas e workers em conjunto. `solutionRevision` coincide com a
publicação que contém o estado; não é comparação isolada para invalidar outras tarefas.

## Pacote de despacho

Arquivo imutável por tentativa. Primeira tentativa pode usar `<task-id>.json`; retries
usam `<task-id>-a<N>.json`, atualizando `dispatchPath`. Caminhos `project.*` relativos
à base do workspace; `prdNotesPath`/`featurePath` relativos à raiz do projeto.
A base absoluta é resolvida na sessão pelo root, sem replicá-la no manifesto.
Para que a chamada contenha somente o caminho do pacote,
o próprio pacote registra `workspaceFromDispatch`, caminho relativo entre sua pasta
**canônica no líder** e a base confirmada. Calcule esse campo no preparo, nunca fixe
o número de `..` por convenção. Filhos derivam a base a partir do path absoluto do
pacote, validam que o líder/catálogo resolvem de volta àquela origem e então resolvem
`PROJECT_ROOT`, `GIT_ROOT`, `PRD_PATH`, `ROADMAP_PATH` e `PRD_NOTES_PATH`. Não dependem
do cwd herdado nem executam pacotes diretamente de uma réplica. Em remapeamento,
o root gera uma tentativa nova com o caminho relativo recalculado.

```json
{
  "version": "1.0",
  "mode": "solution",
  "solutionId": "pagamentos",
  "leaderProjectId": "billing",
  "workspaceFromDispatch": "../../../../../../../..",
  "solutionRevision": 3,
  "runId": "20261108T120000Z-i01",
  "incrementId": "I01",
  "taskId": "checkout-f04-spec",
  "attempt": 1,
  "stage": "spec",
  "project": {
    "id": "checkout",
    "root": "./web-checkout",
    "gitRoot": "./web-checkout",
    "prdPath": "./web-checkout/docs/PRD.md",
    "roadmapPath": "./web-checkout/docs/prd_map_progress.json"
  },
  "featureId": "F04",
  "featurePath": "docs/F04-checkout/",
  "prdNotesPath": "docs/runs/20261108T120000Z-i01/prd-notes.md",
  "lang": "pt-BR",
  "solutionWave": 2,
  "autoAccept": true,
  "providers": [
    {
      "linkId": "L01",
      "projectId": "billing",
      "featureId": "F02",
      "contract": "./api-billing/docs/F02-invoices/spec.md#api-contracts",
      "contractRevision": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "roadmapPath": "./api-billing/docs/prd_map_progress.json",
      "verifiedStatus": "done"
    }
  ],
  "inputHashes": {},
  "options": {
    "execution": "parallel",
    "maxWorkers": 3,
    "workerSlotsGranted": 1,
    "implementationModel": "inherit",
    "testModel": "inherit",
    "modelsAccepted": true,
    "nestedDelegation": false
  },
  "gitLease": "checkout-f04-spec-a1",
  "readFiles": ["./api-billing/docs/F02-invoices/spec.md"],
  "allowedWritePaths": ["docs/F04-checkout/"],
  "requestedChanges": [],
  "acceptanceCriteria": [],
  "commands": []
}
```

`inputHashes` deve conter antes do despacho os hashes reais do PRD, da entrada do
roadmap/decisões relevante, da SPEC/plano/testes quando houver e dos contratos lidos.
Um objeto vazio só é válido antes de preparar a tarefa; não despache assim. Compare
somente campos relevantes do roadmap para não invalidar por progresso de outra feature.
`autoAccept`, modelos e `modelsAccepted` refletem autorização existente; valores do
exemplo não concedem autorização. Guarde solicitado/resolvido e fallbacks por papel
em `options` quando houver seleção além de `inherit`; o retorno registra o efetivo.
`gitLease` é um token lógico verificado no lock real, nunca prova suficiente sozinho.
`lang` no pacote de projeto vem do roadmap/PRD local, que pode ter idioma diferente
do `lang` global da solução. Na criação de PRD, use o idioma já confirmado para aquele
projeto; não traduza um PRD existente como efeito colateral de um incremento.

PRD recebe `requestedChanges`, fatos confirmados, notas anteriores e caminhos locais
autorizados de PRD/checkpoint; não precisa de `featureId`/`featurePath`. SPEC/feature
recebem uma única feature. `providers` descreve só os links de entrada necessários,
sem carregar os PRDs de todos os projetos. `readFiles` externos são de leitura; remapeie
para `read_files` explícitos dos workers. `allowedWritePaths` é relativo ao projeto,
exclui roadmap, `docs/solutions/` e documentos canônicos fora da etapa.

Integração usa `project: null`, `providers`/revisões finais, critérios `AC-Sxx` e
`commands` com `projectId`, comando, recursos e cwd validado. Nenhuma escrita direta
em `SOLUTION_DIR` pelo runner; arquivos gerados vão aos diretórios de teste autorizados.

## Retorno e propostas

Toda janela devolve ao orquestrador um objeto com `taskId`, `attempt`, `status`
(`completed|blocked|failed`), caminhos gerados, revisões lidas, evidências, comandos,
questões pendentes, concessões usadas e modelo solicitado/resolvido/efetivo. Inclua
`proposedMutations`, nunca aplique a proposta diretamente:

```json
{
  "taskId": "checkout-f04-spec",
  "attempt": 1,
  "status": "completed",
  "artifacts": ["docs/F04-checkout/spec.md", "docs/F04-checkout/plan.md", "docs/F04-checkout/tests.md"],
  "proposedMutations": [
    {
      "projectId": "checkout",
      "featureId": "F04",
      "operation": "setSpecPath",
      "mutationId": "checkout-f04-spec-a1-specpath",
      "expected": { "status": "todo", "specPath": "" },
      "changes": { "specPath": "docs/F04-checkout/" }
    }
  ],
  "evidence": [],
  "questions": []
}
```

Operações permitidas: `mergePrd` (criação/mesclagem preservando histórico), `setSpecPath`,
`startFeature`, `finishFeature`. PRD devolve candidatos e diff em `changes`; o root
valida/mescla sob lock. `startFeature` só é aceito após pré-flight/modelos resolvidos;
o root pode prepará-lo antes de despachar `feature`. A janela confirma a aplicação
antes de escrever. `finishFeature` inclui resultado da verificação, commits e decisões.
Integração não altera roadmap: seu resultado atualiza o incremento após validação.
Estado e timestamps são preenchidos pelo escritor único, nunca confiados ao filho.
Cada operação usa `mutationId` estável por `taskId`, tentativa e tipo; o root registra
esse ID em `appliedMutations` após reconciliar a escrita. Não reutilize o ID de início
no desfecho. Repetir o mesmo retorno não repete decisões nem avança estado duas vezes.

## Checkpoints de entrevista

`runs/solution-notes.md` no líder e réplicas: `solutionId`, catálogo/líder confirmados,
perguntas/respostas confirmadas em ordem, decisões, pendências, último passo e próximo
passo. Sem líder, checkpoint durável ainda não existe: informe esse limite na retomada.

`<project>/docs/runs/<run-id>/prd-notes.md`: `projectId`, `runId`, incremento, hashes do
PRD/roadmap de entrada, respostas confirmadas, hipóteses ainda não confirmadas, decisões,
IDs reservados, último passo e próximo passo. O filho PRD escreve só esse checkpoint
local e o PRD. Na retomada, confira hashes e não repita perguntas já respondidas.

## snapshot.json

Gravado por último em cada cópia. `files` mapeia paths relativos ao diretório da solução
para `sha256:<64 hex>` dos bytes exatos; não inclui o próprio `snapshot.json`, locks,
temporários, PRDs, SPECs ou caminhos fora da solução.

```json
{
  "version": "1.0",
  "solutionId": "pagamentos",
  "leaderProjectId": "billing",
  "revision": 3,
  "updatedAt": "2026-11-08T12:00:00Z",
  "files": {
    "SOLUTION.md": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
    "solution.json": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
  }
}
```

Inclua todos os arquivos duráveis reais: `SOLUTION.md`, `solution.json`,
`runs/solution-notes.md`, `runs/<run-id>/state.json`, `dispatch/**` e `integration/**`
quando existirem. Não use o conjunto reduzido do exemplo para omitir arquivos.
`state.solutionRevision` do run atual, `solution.revision` e `snapshot.revision`
coincidem na publicação; estados de runs históricos preservam sua revisão original.
Toda cópia íntegra deve reproduzir exatamente o inventário e os hashes.
