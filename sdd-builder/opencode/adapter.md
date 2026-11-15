# Contrato do adaptador OpenCode 2.2.6

As skills canônicas continuam soberanas para PRD, SPEC, implementação, Git e roadmap.
Este contrato resolve somente ferramentas e execução no OpenCode.

- Consulte `sdd_models` antes de propor modelos. Use `providerID/modelID` exato ou
  `inherit`. Programação e testes são escolhas independentes, aceitas pelo usuário.
- Delegue exclusivamente com `sdd_dispatch`, nunca com `subagent`, shell ou API externa.
  Envie `agent`, `directory` absoluto do projeto, `model`, `gitRoot` absoluto se a unidade
  for mutável, e `packet` com o contexto mínimo completo do contrato canônico.
  `gitRoot` ausente significa pesquisa sem edição. Não envie o histórico da conversa.
- A ferramenta aguarda a sessão filha e retorna sessão, outcome, modelo e mensagens.
  A conclusão técnica da chamada não significa aprovação de TC/AC nem feature done.
  Confira o resultado e as evidências. Falha, interrupção ou pergunta pendente volta ao root.
- Sessões filhas não delegam. No modo solução, o root usa janelas `feature-plan`,
  despacha diretamente as unidades e abre janela `feature-review`, conforme o contrato
  existente de host sem delegação aninhada. Fora de solução, o root assume etapa 3 inline
  quando necessário para despachar workers. Não tente aninhar chamadas.
- Cada janela ocupa um dos três slots globais. Com slots ocupados ou Git concedido,
  aguarde as unidades já iniciadas antes de redisparar. Nunca contorne um bloqueio.
  Mesmo Git serializa unidades mutáveis; o coordenador também aguarda antes de editar,
  commitar ou publicar réplicas. Os locks de roadmap/solução continuam obrigatórios.
- Workers não fazem commit nem escrevem roadmaps. Use as propostas do contrato canônico.
  `blocked` é estado de execução; roadmap local aceita somente todo/in-progress/done.
- Cancelar o pai interrompe a sessão filha. Se houver falha de comunicação, preserve
  a sessão e reconcilie seu estado e seus commits antes de redisparar trabalho.
  Nunca remova locks de outra sessão ou assuma que um timeout encerrou um writer.
- Perguntas são resolvidas no chat principal. Sem modelo selecionado ou permissão,
  retorne bloqueio. Não aprove permissões automaticamente. Acesso a outros projetos
  segue as regras nativas de caminhos externos.
- Caminhos relativos das skills partem do diretório de SKILL.md instalado no pacote;
  caminhos de PRD/SPEC/roadmap partem do projeto alvo. Não crie artefatos no pacote.
