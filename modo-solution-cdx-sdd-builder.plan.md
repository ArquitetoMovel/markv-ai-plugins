# Modo enterprise multiprojeto no sdd-builder

## Resumo

Adicionar uma camada de solução acima do fluxo existente, preservando um PRD e um roadmap por projeto. A solução terá requisitos, incrementos, contratos de integração e dependências entre features de diferentes projetos.

O sdd-builder será o orquestrador persistente: despachará cada revisão de PRD, SPEC de feature e implementação em um contexto separado, validará os resultados e liberará tarefas dependentes.

Decisões confirmadas: suporte a monorepo e multirepo, um PRD ativo por projeto, contextos isolados do harness e avanço contínuo dentro do incremento autorizado, com intervenção somente para decisões pendentes ou bloqueios.

## Arquitetura e interfaces

### Camada de solução

Introduzir a skill solution-builder, carregada pelo sdd-builder somente no modo multiprojeto. O modo será ativado por pedido explícito ou pela presença do manifesto da solução; encontrar vários projetos, isoladamente, não ativará o modo.

Artefatos na raiz coordenadora:

- docs/solution/solution.json: cadastro dos projetos, caminhos dos PRDs e roadmaps, incrementos, referências de features e dependências.
- docs/solution/SOLUTION.md: objetivos, requisitos transversais, decisões e critérios de aceite entre projetos.
- docs/solution/runs/<run-id>/: checkpoint, tarefas despachadas, resultados e evidências da execução.

A raiz coordenadora poderá ser um monorepo ou um repositório dedicado à solução. Cada projeto terá ID estável, raiz local e caminhos explícitos de PRD e roadmap. Caminhos relativos serão resolvidos a partir do manifesto; caminhos absolutos serão aceitos para checkouts externos. A execução validará disponibilidade, permissões, raízes sobrepostas e identidade Git antes de despachar.

Referências globais usarão projectId:F01; IDs e diretórios locais continuarão como hoje. Ondas locais permanecerão restritas ao projeto: “onda 2” de projetos diferentes não significará a mesma etapa global.

### Incrementos e dependências

Cada incremento terá ID estável, objetivo, projetos envolvidos, features vinculadas e critérios de aceite da solução. Features descobertas durante a atualização de PRD serão vinculadas ao incremento antes de gerar suas SPECs.

O grafo combinará dependências locais com dependências entre projetos:

- Contrato: a SPEC consumidora exige um contrato fornecedor aceito e identificado por revisão.
- Implementação: a implementação consumidora exige a feature fornecedora concluída e verificada.
- Integração: a conclusão do incremento exige os testes entre projetos aprovados.

Dependências locais existentes continuarão exigindo implementação prévia, preservando o comportamento atual. A antecipação de SPEC por contrato será explícita no modo solução.

Contratos transversais terão produtor, consumidores, referência ao artefato e revisão. A SPEC do fornecedor produzirá o contrato; o orquestrador verificará sua consistência antes de liberar consumidores. Ciclos ou contratos incompatíveis bloquearão as tarefas afetadas e exigirão divisão ou revisão do incremento.

## Execução, persistência e compatibilidade

### Contextos separados

Cada tarefa receberá um pacote persistido contendo identificação da solução, incremento, projeto, feature e etapa; caminhos absolutos; escopo de leitura e escrita; requisitos pertinentes; contratos; dependências; escolhas de modelos e critérios de término.

O contexto será novo por:

- Revisão de PRD de um projeto em um incremento.
- SPEC de uma feature.
- Implementação de uma feature, preservando as unidades internas já existentes.
- Validação de integração do incremento.

Não será herdado o histórico completo do orquestrador. O retorno conterá estado, artefatos, revisões de entrada, alterações, evidências, bloqueios e decisões necessárias.

O orquestrador verificará as capacidades reais do harness. Com delegação aninhada, o feature-builder poderá coordenar seus workers. Sem ela, solicitará unidades ao orquestrador principal, que fará os despachos. Sem qualquer mecanismo de contexto isolado, a tarefa ficará aguardando handoff externo persistido; execução inline não será apresentada como isolamento.

### Agendamento e retomada

Persistir tarefas com estados pending, running, completed, blocked, failed e cancelled, separados dos status locais de features.

Cada tarefa terá identidade estável, tentativa, revisões de entrada, identificação de sessão quando disponível, resultado e evidências. O orquestrador registrará a intenção antes do despacho e validará os artefatos antes de aceitar a conclusão.

Na retomada, reconciliará checkpoints, sessões existentes, arquivos e commits antes de repetir qualquer trabalho. Uma tarefa running sem retorno não será automaticamente considerada falha nem redisparada enquanto puder haver um writer ativo.

Aplicar um orçamento global de workers, padrão 3, limitado pelo host e compartilhado com os workers internos. Projetos independentes poderão avançar em paralelo. No mesmo repositório Git, etapas mutáveis serão serializadas na primeira versão; recursos externos compartilhados também terão exclusão.

### Escritores e evolução incremental

O progress-tracker continuará sendo o contrato canônico dos roadmaps locais. O orquestrador da solução será o único escritor do checkpoint global.

Para tarefas delegadas em modo solução, acrescentar uma modalidade de retorno de mutações propostas: PRD, SPEC e implementação retornam alterações de roadmap, e o orquestrador as aplica sob lock, releitura e troca atômica. Isso evita contrariar a atual proibição de subagentes paralelos escreverem no roadmap.

Atualizar o fluxo incremental de PRD para preservar IDs, specPath, status e evidências existentes. Novas features receberão novos IDs; remoções serão registradas sem apagar histórico. Alterações em features concluídas exigirão reabertura explícita ou uma nova feature de evolução.

O checkpoint registrará revisões dos documentos e contratos. Mudanças relevantes invalidarão tarefas consumidoras ainda não aceitas e bloquearão sua continuação até reconciliação. Features já concluídas não serão reabertas silenciosamente.

O modo de projeto único manterá seus caminhos, schema e comportamento. Não haverá clone, criação de branch, push, merge ou deploy automáticos.

## Entrega e validação

Implementar em quatro incrementos do plugin:

1. Contratos: skill de solução, formatos versionados, exemplos monorepo/multirepo e protocolo de checkpoint.
2. Fluxo documental: resolução explícita de projetos, atualização incremental de PRD e SPEC isolada com contratos transversais.
3. Execução: scheduler global, delegação conforme capacidades do host, implementação, integração e retomada.
4. Distribuição: sincronizar agentes tradicionais e Copilot, atualizar README, manifests e entradas de marketplace para 1.4.0.

Adicionar validadores e fixtures para verificar os contratos persistidos, sem criar um serviço de execução próprio. Cobrir:

- Projetos com IDs locais iguais, caminhos externos e checkouts ausentes.
- Incremento envolvendo API e frontend: contrato → SPEC consumidora → implementação → integração.
- Ciclos, referências inexistentes e mudança de contrato após despacho.
- Atualização de PRD preservando features e progresso anteriores.
- Concorrência entre repositórios e serialização dentro do mesmo repositório.
- Interrupção antes/depois do despacho, retorno duplicado e resultado desatualizado.
- Harness sem delegação aninhada ou sem contexto isolado.
- Regressão do fluxo atual de projeto único e consistência dos manifests.

O incremento da solução somente será concluído quando suas features estiverem verificadas e os critérios entre projetos tiverem evidências aprovadas. Sucesso local com integração falhando será reportado como incremento incompleto.

