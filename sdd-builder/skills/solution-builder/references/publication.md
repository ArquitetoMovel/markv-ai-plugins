# Publicação, locks e retomada

## Autoridade e locks

O único escritor global é o orquestrador da solução. Réplicas nunca se tornam líderes
por timestamp ou revisão maior. A garantia de exclusão é local ao workspace compartilhado;
clones independentes não têm lock distribuído e exigem coordenação externa.

1. Lock de solução: `mkdir <SOLUTION_DIR>/solution.lock`, atômico em POSIX. Grave owner
   com host, PID quando disponível, `runId`, tarefa, token e instante UTC. Handles nativos
   de sessões e heartbeat ficam aqui, sem replicação. Mantenha um coordenador vivo por
   solução durante a execução; publicação usa esse owner, não um segundo coordenador.
2. Lock Git: descubra a pasta Git comum com `git -C <gitRoot> rev-parse --git-common-dir`,
   resolva caminho absoluto e use `<git-common-dir>/sdd-builder.lock/`. Identidade real
   compartilhada evita duas concessões para o mesmo monorepo ou symlink. Esse lock é
   um diretório próprio, nunca `.git/index.lock`. Inclua `runId`, tarefa, owner/token e
   concessão de workers no registro. Outras soluções usam a mesma primitiva.
3. Ordem: coordenador de solução → Git(s) em ordem lexicográfica dos caminhos reais →
   lock de roadmap `<project.root>/docs/prd_map_progress.lock`. Tarefa recebe concessão
   Git reservada antes do despacho; workers subordinados usam o token, não readquirem
   o lock. Não aguarde escrita global segurando Git: o filho devolve proposta, termina
   seus workers e devolve a concessão antes da aplicação/publicação pelo root.
4. Reserve Git também para PRD, SPEC, roadmap e escrita das réplicas. Para publicação,
   espere writers afetados terminarem e congele novos despachos. Não retenha um lock
   Git parcial enquanto espera outro: libere as concessões adquiridas se o conjunto
   não estiver disponível e reagende em ordem, evitando bloqueio entre soluções.
5. `mkdir` ocupado: releia owner, aguarde 2 segundos, no máximo 5 tentativas. Depois
   registre bloqueio e diagnóstico. Idade acima de 10 minutos é suspeita, não prova de
   abandono: confira writer/sessões/heartbeat e peça confirmação antes de remover lock
   alheio. Owner ausente recebe um ciclo de tolerância e depois o mesmo diagnóstico.
6. Só remova seu próprio lock, conferindo token, após aguardar/encerrar writers e
   comandos. Falha/timeout não autoriza roubar lock ou deixar comandos órfãos.

## Publicação de uma revisão

Não há transação atômica entre repositórios. O snapshot detecta uma cópia parcialmente
gravada; ele não torna uma publicação inteira atômica. Cada revisão segue este protocolo:

1. Sob o lock do líder, valide o snapshot anterior e reconcilie qualquer publicação
   pendente antes de mudar documentos. Reserve Git(s), confira estado inicial e evite
   tocar alterações preexistentes. Em inicialização, confira a ausência de solução
   conflitante no destino.
2. Prepare a nova revisão em temporários no mesmo filesystem do líder. Incremente
   `solution.revision`, atualize `state.solutionRevision` do run atual e timestamps;
   runs históricos preservam seu checkpoint/revisão original. Valide schemas, caminhos,
   referências, grafo e inventário. Inclua somente artefatos globais listados no contrato.
3. Calcule hashes dos bytes finais. Grave um journal transitório em
   `solution.lock/publication.json` com revisão de origem/destino, inventários anterior
   e novo, participantes e destinos pendentes. Prepare o snapshot novo em temporário.
   O journal não é replicado nem versionado.
4. Troque cada arquivo canônico com temporário + `mv` no mesmo diretório; publique
   `snapshot.json` por último no líder e confira todos os hashes. O journal registra
   a etapa atingida; mantenha a revisão anterior íntegra nos temporários do lock até
   terminar a publicação para permitir diagnóstico após uma interrupção.
5. Em cada projeto, valide o snapshot de origem e o destino. Uma réplica íntegra de
   revisão anterior pode ser atualizada; edição local divergente não é sobrescrita
   automaticamente. Copie os bytes finais via temporários, confira hashes e troque o
   snapshot por último. Ao remover artefatos, retire só paths do inventário anterior
   geridos pelo plugin, após checar integridade; nunca apague diretórios/documentos
   desconhecidos para fazer o inventário bater. Não copie locks ou temporários.
6. Releia todas as cópias: identidade, líder, revisão, conjunto de arquivos e hashes
   devem coincidir. Só então registre a publicação como concluída no journal local,
   libere concessões Git e autorize novos despachos. Não altere `state.json` depois de
   calcular o snapshot sem gerar/publicar revisão nova.
7. Em erro, mantenha diagnóstico da publicação pendente no journal e no relatório.
   Nenhum despacho novo ou conclusão de incremento até reconciliação. Ao encerrar,
   preserve temporários necessários ao diagnóstico; se não puder manter owner ativo,
   exponha o handoff e deixe a retomada diagnosticar o lock em vez de apagá-lo às cegas.

Toda escrita durável global, inclusive checkpoint, despacho e atualização de estado,
faz parte de uma revisão publicada. O manifesto de bootstrap pode ter `links` e
incrementos ainda sem features, mas não libera tarefas antes da validação dos IDs.

## Retomada e recuperação

- Snapshot íntegro do líder + réplica antiga/ausente: complete a publicação a partir
  do líder, validando contra o inventário anterior. Não copie PRDs/SPECs de um projeto
  para o outro. Participante sem checkout continua bloqueando publicação.
- Interrupção antes de trocar snapshot do líder: use journal e temporários íntegros
  para terminar a mesma revisão ou restaurar a anterior. Se não houver bytes/hash
  suficientes para provar integridade, bloqueie e peça reconciliação; não escolha
  arbitrariamente arquivos de cópias diferentes.
- Snapshot novo do líder + falha no meio de uma réplica: compare os bytes do destino
  com inventários anterior e novo e journal. Complete somente alterações atribuíveis
  à publicação interrompida. Sem essa prova, preserve o destino e sinalize divergência.
- Hash divergente no líder, réplica com revisão superior ou edição manual: não use
  maior timestamp/revisão como autoridade. Mostre os paths divergentes e reconcilie
  explicitamente, publicando revisão nova depois de validar a decisão.
- Líder ausente: leitura de réplica íntegra é permitida. Escrita fica bloqueada até
  restaurar o líder ou confirmar troca de líder, provar que o coordenador anterior
  parou e validar uma réplica íntegra de origem. Atualize `leaderProjectId`, incremente
  a revisão e publique em todos os participantes, incluindo o antigo líder quando
  restaurado; até isso ocorrer não libere execução distribuída.
- Descoberta em nova máquina: confirme/remapeie base do workspace e caminhos externos,
  valide os `gitRoot` reais; não use paths absolutos antigos ou handles de sessão como
  autorização de execução.
- `running`: confira lock, sessão e estado de arquivos/commits. Writer vivo não é
  redisparado. Writer encerrado exige tentativa nova e revalidação de entradas; não
  aceite evidência antiga para código que mudou. `acceptedAttempt` impede reaplicação
  do retorno final; `appliedMutations` distingue operações de início e desfecho na mesma
  tentativa e evita repetição dos apêndices de decisões.

## Git e versionamento

Arquivos duráveis ficam em caminhos versionáveis de todos os projetos. Verifique
`git check-ignore` para destinos; não force inclusão de paths ignorados sem resolver
a regra aplicável. Locks/temporários/sessões locais nunca são adicionados ao índice.
Sincronização em disco e commits são operações distintas. Se commits documentais
forem autorizados, faça um por Git afetado (um commit pode conter as cópias de vários
projetos do mesmo monorepo), usando apenas arquivos do inventário da solução e paths
explícitos relativos àquele `gitRoot`. Confira stage alheio antes de commitar e nunca
o incorpore ou limpe. Publicação não executa push. Commits de features permanecem
separados e preservam mudanças preexistentes.
