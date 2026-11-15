# Contrato do adaptador OpenCode 2.2.6

As skills canônicas continuam soberanas para PRD, SPEC, implementação, Git e roadmap.
Este contrato resolve somente ferramentas e execução no OpenCode.

- Programação e testes usam `inherit` por padrão, sem pergunta de modelo. Overrides
  opcionais alteram somente o papel informado. Consulte `sdd_models` para resolver
  overrides, restrições ou pedido de opções; use `providerID/modelID` exato.
- Delegue exclusivamente com `sdd_dispatch`, nunca com `subagent`, shell ou API externa.
  Envie `agent`, `directory` absoluto do projeto, `gitRoot` absoluto se a unidade
  for mutável, e `packet` com o contexto mínimo completo do contrato canônico.
  `model` é opcional e usa `inherit` quando omitido: modelo do pai ou padrão do host
  quando o pai não o expõe. Preserve origem, preferências e fallbacks no pacote.
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
- Perguntas necessárias são resolvidas no chat principal. Sem preferência de modelo,
  prossiga com herança. Override incompatível sem fallback autorizado ou falta de
  permissão retorna bloqueio; sem interação, informe o motivo sem espera indefinida.
  Não aprove permissões automaticamente. Acesso a outros projetos segue as regras nativas.
- Caminhos relativos das skills partem do diretório de SKILL.md instalado no pacote;
  caminhos de PRD/SPEC/roadmap partem do projeto alvo. Não crie artefatos no pacote.
