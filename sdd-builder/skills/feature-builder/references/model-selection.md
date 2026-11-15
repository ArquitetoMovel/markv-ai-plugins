# Plano de execução e modelos por harness

Contrato canônico da política de modelos na implementação. Aplique depois de carregar
spec/plano/testes, conferir dependências e identificar as stacks, antes de marcar
`in-progress`, escrever código/testes ou despachar workers de implementação.

## 1. Herança como padrão

`implementation-model=inherit` e `test-model=inherit` são os padrões documentados.
Sem preferência, apresente o plano e execute o trabalho solicitado sem perguntar por
modelos. Um override válido altera somente o papel informado; o outro continua herdado.
O mesmo modelo pode atender aos dois papéis. Modelos diferentes nunca são obrigatórios.

Os perfis usam `model: inherit` quando o formato aceita esse campo; nos demais, a herança
é implícita. A resolução segue a semântica do host, inclusive em contextos aninhados;
`inherit` não fixa um ID nem garante o modelo da sessão principal em toda a árvore.
Nenhum especialista fixa provedor ou família de modelo. Não selecione automaticamente
um modelo mais leve para testes sem política aceita: autoria, diagnóstico e validação podem exigir tanta
capacidade quanto implementação. Separar papéis e contextos continua útil com um só LLM.

Respeite as restrições obrigatórias do ambiente e, dentro delas, esta precedência:

1. Overrides explícitos na invocação atual.
2. Preferências já aceitas para o escopo da execução/projeto/solução.
3. `inherit` para cada papel ainda sem preferência.

Registre a origem por papel como `explicit`, `preference` ou `default`. Aplicar o padrão
não é registrar aceite explícito do usuário. Preserve preferências e fallbacks válidos
na retomada e nos pacotes de despacho; não repita perguntas já resolvidas. Uma nova
escolha explícita substitui a preferência anterior daquele papel.

## 2. Identificar harness e capacidades

Detecte o ambiente pela identificação da sessão, metadados das ferramentas e configuração
local relevante. O modelo da conversa e a presença de `.claude/`, `.cursor/` ou `.codex/`
no repositório não comprovam qual harness está ativo.

Registre harness, fonte da identificação, delegação, concorrência, profundidade e seleção
nativa por chamada, perfil ou sessão. Use o schema real da ferramenta e confira se um
override exige contexto novo ou parâmetro específico. Não invente chamadas universais.

Consulte o catálogo apenas quando necessário para resolver overrides, restrições ou um
pedido de opções. Sem overrides, a falta de catálogo ou de identificação precisa do
host não bloqueia a herança nativa já suportada. Se faltar capacidade indispensável ao
despacho, informe essa limitação e aplique os fallbacks de execução do fluxo; no modo
solução, preserve a obrigação de contexto isolado.

Para resolver uma escolha, consulte nesta ordem:

1. Catálogo/enum e capacidades expostos pelas ferramentas da sessão.
2. Comandos de consulta documentados para o harness instalado e perfis existentes.
   Leia somente a configuração necessária, sem expor credenciais.
3. Documentação oficial para esclarecer nomes e mecanismos, sem presumir acesso da conta.

Resolva nome de apresentação → valor aceito pelo mecanismo real do host. Um alias por
chamada e um ID completo no perfil podem ter regras distintas. Não copie IDs entre
harnesses nem substitua uma versão solicitada por alias móvel sem autorização.
Sem catálogo consultável, use outra fonte verificável do host; se a escolha explícita
continuar não verificável, devolva essa incompatibilidade. Não execute trabalho para
sondar disponibilidade nem substitua a escolha pelo padrão.

## 3. Apresentar o plano e continuar

Prepare um plano concreto e curto a partir de `plan.md`, sem o reescrever. Mostre:

- Feature, fases, unidades, especialistas e dependências.
- Paralelismo elegível, integrações exclusivas e validações de cada fase.
- Harness, modo efetivo, limite de workers e limitações relevantes.
- Modelo e origem por papel. `implementation-model` cobre `implementation` e `integration`;
  `test-model` cobre `test-authoring` e `test-execution`, inclusive retries e verificação
  final. Nenhum deles troca o modelo do orquestrador.

Exemplo sem preferência de modelos:

```text
Plano de implementação: F03
Execução: parallel | Máximo de workers: 3, conforme capacidade do host
Fase 1: contratos e registros, em sequência.
Fase 2: implementação e autoria de testes independentes; execução após convergência.
Fase 3: integração, suíte completa e critérios de aceite.
Programação: inherit (origem: default).
Testes: inherit (origem: default).
Vou iniciar com a herança do host. Overrides por papel são opcionais.
```

Apresente o plano e prossiga quando padrões e overrides forem aplicáveis. Não abra
seletores obrigatórios nem aguarde confirmação; não peça o segundo papel só por estar ausente.
Em batch/CI ou outra execução sem interação, execute com os padrões válidos normalmente.

Pergunte somente para resolver uma escolha explícita ou preferência incompatível,
instruções contraditórias ou uma restrição aplicável que nenhuma alternativa atenda,
quando não houver fallback previamente autorizado. Pare o despacho afetado até resolver;
preserve as barreiras de dependência antes de iniciar a implementação. Sem interação,
retorne erro/bloqueio claro com papel, motivo e alternativas reais, sem espera indefinida.
Enquanto houver essa incompatibilidade no plano inicial, prepare apenas leituras e
decomposição; não altere arquivos, despache implementação ou marque `in-progress`.

Silêncio, timeout ou opção preselecionada não autorizam substituir uma escolha explícita.
Isso não impede aplicar `inherit` a um papel sem preferência, conforme o padrão acima.

## 4. Aplicar a política sem alterar o ambiente global

- Aplique o modelo resolvido em cada worker pelo mecanismo nativo, inclusive retries,
  integração e correções finais. Prefira override por chamada quando suportado.
- Se a seleção depender de perfil, use um perfil existente que preserve contrato,
  ferramentas e escopo do worker. Não reescreva perfis compartilhados, plugin instalado
  ou configuração global. Não troque o orquestrador para simular seleção por worker.
- `inherit` usa o mecanismo de herança do host, sem enviar um ID literal inválido.
  O nome do agente ou o texto do prompt não comprova seleção de LLM.
- Sem seleção por worker, informe a herança efetiva e prossiga se não houver preferência
  incompatível. Em single-project, use inline/sequencial quando necessário e permitido;
  em solução, mantenha o isolamento obrigatório. Só ofereça ajuste manual quando uma
  escolha explícita exigir essa intervenção.
- Modelo escolhido indisponível ou substituição imposta pelo host que contrarie uma
  preferência/restrição exige alternativa aceita, salvo fallback já autorizado para
  aquele papel. Pare novos despachos afetados, aguarde/encerre workers, preserve diffs
  e resolva a incompatibilidade. A resolução normal de `inherit`, dentro das restrições,
  é parte do padrão e não exige nova confirmação.
- Falha de teste não autoriza aumentar o modelo automaticamente. Trocar worker ou modelo
  não reinicia o orçamento de retries.

No relatório e nos retornos, diferencie origem, modelo **solicitado** (override/preferência
ou `inherit` padrão), **resolvido** e **efetivo** informado pelo host. Se o efetivo não for
exposto, escreva `não informado pelo host`; não deduza aplicação nem anuncie economia.

## 5. Otimização opcional

Ofereça opções quando o usuário pedir. Use o catálogo atual e justificativas verificáveis,
sem dupla de modelos recomendada universalmente nem promessa de economia por papel.
Roteamento automático entre modelos exige política previamente aceita no escopo, com
modelos/provedores permitidos, limites de custo e fallbacks definidos. Sem essa política,
mantenha herança e overrides. Otimizações devem ser avaliadas em tarefas representativas,
comparando qualidade, defeitos detectados, custo total, tempo, retries e intervenção
humana; a aprovação de testes gerados pelo próprio fluxo não basta como evidência.

## Referências oficiais

- [Seleção em subagentes Claude Code](https://code.claude.com/docs/en/sub-agents#choose-a-model).
- [Subagentes Cursor](https://cursor.com/docs/subagents#model-configuration).
- [Configuração de agentes Copilot](https://docs.github.com/en/copilot/reference/custom-agents-configuration).

## OpenCode 2.2.6

Com o adaptador `opencode-sdd-builder`, `sdd_dispatch` usa `inherit` por padrão quando
`model` é omitido. Para overrides, consulte `sdd_models` e use `providerID/modelID` exato.
A sessão filha herda o modelo da sessão pai ou o padrão do host quando o pai não o expõe;
o retorno distingue solicitado/resolvido/efetivo. O coordenador mantém seu modelo.
O adaptador serializa Git e limita três janelas globais, sem delegação aninhada. A skill
`sdd-opencode` define o mapeamento de ferramentas e a recuperação de locks.
