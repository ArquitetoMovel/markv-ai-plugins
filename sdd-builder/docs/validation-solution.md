# Validação do modo solução 1.4.0

Esta versão distribui instruções Markdown e manifests JSON, sem scheduler executável
próprio. Há duas verificações distintas: integridade do pacote no repositório e ensaios
de comportamento em sessões reais dos hosts. Não registre um ensaio como aprovado
apenas porque as instruções existem ou uma simulação de grafo passou.

## Verificação do pacote

- Parsear os três manifests do plugin e os quatro marketplaces. Comparar nome, versão
  `1.4.0`, descrição e keywords do plugin; comparar a entrada completa nos marketplaces.
  Preservar os nomes de marketplace específicos de cada host.
- Claude/Cursor sem `agents`/`skills` explícitos. Copilot com
  `agents: "copilot-agents/"` e `skills: ["skills/"]`.
- Todo agente tem duas cópias com corpos idênticos. Claude/Cursor mantém `model: inherit`,
  ferramentas por host e referências `sdd-builder-plugin:<skill>` existentes. Copilot
  usa `.agent.md`, tools minúsculas em array JSON, sem `model` nem `skills` no frontmatter.
- Toda skill tem `name`/`description`; referências locais e links Markdown do plugin
  resolvem. Parsear os exemplos `json` completos, sem tratar hashes ilustrativos como reais.
- Conferir ausência de paths legados no diretório neutro, placeholders de implementação,
  escrita global por workers e regressão de schema do roadmap `1.0`.
- Rodar `git diff --check`; conferir que mudanças em outros plugins e arquivos
  preexistentes do usuário não entraram no escopo.

## Fixture de ensaio

Em diretório temporário fora do marketplace, prepare um workspace **sem `.git`**,
com `api-billing/` e `web-checkout/` como repositórios Git próprios. Prepare também
uma variante com esses diretórios em um único monorepo. Não use projetos reais como
fixture destrutiva nem faça push. O ensaio deve informar modelos/recursos disponíveis.

Catálogo: `billing` (platform) e `checkout` (product), líder `billing`, solução
`pagamentos`, incremento `I01`. Ambos podem ter uma feature `F01`. Billing oferece
`F02`; Checkout consome em `F04` e tem `F05` dependente local de `F04`.
Use contrato HTTP com payload e erros observáveis e um critério `AC-S01` que verifica
criação da fatura e exibição do comprovante. Fixtures de código/testes ficam nos
projetos de ensaio, jamais em `docs/solutions/`.

## V01: inicialização com prompt completo

Invoque `sdd-solution-builder` no workspace com catálogo, caminhos, objetivo, líder e
escopo de I01. Espere validação de Git por projeto e resumo de confirmação. Depois:

- Workspace continua sem `.git` e sem `docs/` obrigatório.
- Fonte canônica em `api-billing/docs/solutions/pagamentos/` e cópia em
  `web-checkout/docs/solutions/pagamentos/`, com mesmos bytes, revisão e hashes.
- Manifesto identifica líder e projetos; locks/temporários não estão no inventário Git.

## V02: entrevista sem detalhes e retomada

Invoque sem descrição. Espere sondagem dos filhos imediatos e perguntas mínimas,
uma por vez. Antes de líder confirmado, respostas ficam na sessão. Confirme catálogo
e líder; depois de cada resposta, confira `runs/solution-notes.md` publicado nos dois
projetos. Interrompa e reabra sessão; respostas persistidas não são perguntadas de novo.
Checkpoint ainda inexistente deve ser informado, nunca reconstruído como resposta confirmada.

## V03: descoberta, cópias e múltiplas soluções

Inicie pelo workspace, pelo líder e por `web-checkout`. Três entradas devem resolver
a mesma solução/líder. Réplicas não aparecem como soluções duplicadas. Adicione outra
solução ao projeto e espere seleção explícita. Remova temporariamente o checkout do
líder: permita inspeção de réplica íntegra, bloqueie escrita e não promova automaticamente.

## V04: separação de escopos e caminhos

Gere PRDs e SPECs. Confira `PRD.md`, roadmap, `Fxx-*/{spec,plan,tests}.md` e
`docs/runs/<run-id>/prd-notes.md` em cada projeto. `docs/solutions/` contém apenas
visão, manifesto, notas/estado/despacho globais, snapshots e evidências de integração.
Nenhuma cópia do PRD/SPEC local entra ali. Links preservam referência e revisão.

Teste `billing:F01` e `checkout:F01`, projeto externo por caminho absoluto, nova base
de checkout, symlink e caminho que escapa da raiz. Resolver contra a base confirmada,
nunca contra a pasta do manifesto ou cwd herdado. Pacote no líder precisa resolver a
base via `workspaceFromDispatch` recebendo somente seu path; pacote numa réplica não
é executado diretamente. Destino ausente, ignorado pelo Git ou colisão real bloqueia.

## V05: revisão incremental de PRD

Parta de feature `done` com `specPath`, evidência e decisão. Peça I02 com feature nova
e uma removida. Confira preservação dos campos, novo ID acima do máximo histórico,
nenhuma renumeração e remoção anotada `no longer in PRD`, sem apagar status.
Peça alteração em feature `done` sem autorizar reabertura: espere bloqueio/proposta
e preservação do PRD anterior. Confirme evolução ou reabertura e confira o diff.
Checkpoint da entrevista deve ficar só no projeto afetado; seção 8 só usa IDs locais.

## V06: portões e integração ponta a ponta

Tente SPEC de `checkout:F04` antes de existir contrato validado de `billing:F02`:
espere bloqueio, sem endpoint inventado. Gere/valide a SPEC fornecedora e publique
hash real; a SPEC consumidora agora pode ser gerada antes da implementação externa,
desde que as dependências locais/Foundation estejam prontas.

Tente implementar consumidor com provider ainda `todo`: espere bloqueio antes de editar.
Implemente fornecedor, verifique `done`/evidências, depois implemente consumidor.
Mesmo com todas as features `done`, comando vazio ou integração indisponível mantém
I01 bloqueado. Só aceite `done` após os critérios AC-Sxx passarem nas revisões finais,
com comando, cwd, saída, teste e resultado registrados e publicados nos participantes.

## V07: cálculo de onda e anomalias do grafo

Use este caso determinístico para detectar implementação incompleta da fórmula:

```text
billing:F02: onda interna 4, sem provider externo
checkout:F04: onda interna 1, provider billing:F02
checkout:F05: onda interna 2, dependência local checkout:F04
Esperado: ondas da solução 4, 5 e 6, respectivamente.
```

Atraso externo precisa propagar também ao dependente local. Adicione link inverso
formando ciclo e depois um ID inexistente: espere bloqueio das tarefas afetadas.
Dependência fora do incremento precisa estar satisfeita ou ser incluída explicitamente,
sem expansão silenciosa. Foundations greenfield são sequenciais até estabilizar a base.

## V08: invalidação de contrato

Depois do despacho do consumidor, altere o contrato fornecedor e seu hash. Espere
suspensão dos consumidores ainda incompletos, espera/encerramento dos writers e
rejeição de retorno da revisão antiga. Replaneje sob revisão nova, preservando diffs.
Mudança de consumidor já `done` pede análise de impacto e evolução/reabertura.
Atualização global causada só por progresso de outra tarefa não invalida trabalho
cujos hashes/precondições continuam iguais.

## V09: escritor único, idempotência e locks

Inspecione instruções e efeitos de cada janela: filhos PRD/SPEC/feature só devolvem
propostas; root aplica roadmap e escreve documentos globais. Trabalhador nunca commita.
Retorne duas vezes a mesma tentativa: `specPath`, estados e decisões não são duplicados.
Interrompa após gravar roadmap e antes do estado global: retomada reconhece diff já
aplicado, não repete decisões nem apaga progresso de outra feature.

Faça lock ocupado, owner ausente e owner antigo ainda com writer vivo. Respeite retries,
diagnóstico e confirmação para remover lock alheio; idade sozinha não prova abandono.
Tarefa `running` com writer vivo nunca é redisparada. Confira ordem solução → Git →
roadmap e devolução da concessão Git antes de aguardar a publicação de uma proposta.

## V10: publicação interrompida e divergência

Interrompa antes/depois do snapshot do líder e no meio de uma réplica. Hash inválido
deve impedir aceitar a cópia como íntegra e bloquear novos despachos/conclusão.
Com journal e inventários íntegros, retome a mesma revisão; sem prova da origem dos
bytes, preserve os arquivos e peça reconciliação. Confira cópias finais idênticas.

Edite uma réplica manualmente, apresente revisão superior ou deixe participante ausente:
nunca sobrescreva divergência nem escolha por timestamp. Troca de líder precisa ser
confirmada, com coordenador anterior encerrado e nova revisão publicada em todos.
Lock, temporário e ID nativo de sessão não podem aparecer em snapshot/commit.

## V11: concorrência, monorepo e commits

Execute tarefas independentes em Git distintos: paralelismo permitido dentro do teto.
Na variante monorepo, tarefas mutáveis de projetos distintos devem esperar a mesma
concessão Git. Publicação também espera writers terminarem. No máximo três janelas
e workers internos ativos somados, sem conceder três slots novos para cada feature.

Teste índice com stage alheio: commit bloqueia sem incluir/resetar o trabalho alheio.
Commits da feature só incluem paths da fase/projeto e não as cópias da solução.
Suíte roda na raiz do projeto. Mensagem `F01 fase 1` em outro projeto do monorepo
não basta para pular fase. Cancelamento encerra/aguarda workers antes de liberar locks.

## V12: capacidades do harness

- Com delegação aninhada: slots de filhos são reservados no orçamento global.
- Sem delegação aninhada: `feature-plan` termina antes de o root despachar especialistas;
  finalização passa por `feature-review` em contexto novo, com evidências finais reais.
- Com apenas um slot: planejamento termina antes do worker, sem deadlock de coordenadores.
- Sem interação em filhos: perguntas/modelos voltam à sessão principal, respeitando
  escolhas já aceitas; nenhuma escolha é feita por silêncio.
- Sem contexto isolado ou sem subagentes por preferência: handoff persistido e tarefa
  `blocked`, sem executar projeto inline no chat global. Não diga "isolado" quando o
  mecanismo nativo herda o histórico completo.

## V13: regressão single-project e hosts

Sem solução descoberta/pedido multiprojeto, percorra PRD → SPEC single/batch → feature.
Paths e schema antigos permanecem; apenas os escritores locais autorizados gravam o
roadmap. Fallback inline local continua disponível quando aplicável. Não crie
`docs/solutions/` como efeito colateral de fluxo local.

Repita os ensaios relevantes em Claude Code, Copilot CLI e Cursor conforme suas
capacidades. Registre ferramenta real, modo efetivo, limitações e handoffs; instalação
válida não comprova que todos os hosts oferecem delegação/isolamento equivalente.

## Registro de execução dos ensaios

Para cada Vxx executado, anote host/capacidades, fixture/revisões, ações, evidências,
resultado `passed|failed|blocked|not-run`, paths/commits e limitações. Checks estáticos
do pacote podem ser feitos no marketplace sem sessões externas; V01–V13 exigem os
ensaios descritos e não são aprovados por mera leitura deste documento.

### Verificação estática desta implementação (2026-11-08)

Foram conferidos os sete manifests e a preservação dos demais plugins, os 13 pares
de agentes com corpos idênticos, o frontmatter YAML de 32 arquivos (agentes e skills),
dez exemplos JSON completos, 21 links locais e blocos Markdown. A identidade do líder,
revisões e resolução relativa do pacote também foram verificadas. `git diff --check`
passou. Os ensaios V01–V13 em sessões reais dos hosts estão `not-run`; essa verificação
estática não comprova comportamento do LLM nem capacidades de delegação dos hosts.
