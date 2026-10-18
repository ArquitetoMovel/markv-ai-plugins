# Execução por unidades independentes

Referência canônica de agendamento do `feature-builder`. Leia ao preparar cada fase.
O contrato enviado aos workers está na skill [work-unit](../../work-unit/SKILL.md).

## Opções da invocação

São instruções interpretadas pela skill, não flags de um executável nem configurações
globais do host. Valem só para a execução atual, inclusive retries e verificação final.

| Opção | Padrão | Semântica |
| --- | --- | --- |
| `execution=parallel` ou `execution=sequential` | `parallel` | Paralelo somente entre unidades elegíveis da mesma fase; sequencial mantém um worker ativo por vez. |
| `max-workers=N` | `3` | Inteiro positivo. Limita todos os workers ativos, incluindo testes, ao menor valor entre N e os slots disponíveis no host. |
| `test-model=inherit` ou `test-model=<ID>` | `inherit` | Modelo dos workers de autoria e execução de testes, inclusive validações de fase e finais. Não altera o modelo de implementação ou do orquestrador. |

Aceite equivalentes como `modo paralelo`, `sem paralelismo`, `no máximo 2 agentes` e
`use haiku nos testes`. `max-workers=1` serializa sem eliminar os contextos separados.
`não use subagentes` força execução inline e sequencial; uma seleção de modelo de testes
fica inaplicável nesse caso. Registre opções inválidas/contraditórias em Overrides ignored
e mantenha o padrão da opção afetada. Restrições explícitas de não delegar ou não
paralelizar sempre prevalecem. Em sequencial, o teto efetivo de workers é 1.

`modelo menor` sem um ID não identifica um modelo portável: peça ao usuário a escolha
entre os modelos disponíveis enquanto prepara unidades independentes dessa escolha.
Sem escolha, mantenha `inherit` e não anuncie redução de custo. Não fixe tabela de preços
ou mapeamento universal entre aliases de provedores.

## Capacidade do host e seleção efetiva do modelo

Antes de despachar, confira as ferramentas realmente disponíveis na sessão: delegação,
concorrência, profundidade permitida e seleção de modelo por chamada. Use a ferramenta
nativa (Agent/Task, agent ou equivalente); não invente parâmetros ou chamadas.

- Prefira override de modelo **na chamada do worker de testes** quando suportado. Passe
  o ID escolhido também nos retries; escrever `use modelo X` no prompt não troca o LLM.
- `inherit` pede o modelo da sessão que coordena a fase, pelo mecanismo suportado. Quando
  só houver herança implícita, não envie literalmente `inherit` como ID desconhecido.
- Se o host só aceitar seleção por perfil, use um perfil de testes já configurado com o
  modelo solicitado. Não reescreva o plugin instalado, o perfil compartilhado ou a
  configuração global durante a execução: isso afetaria outras chamadas concorrentes.
- Modelo indisponível, substituição imposta pelo host ou ausência de seleção por worker:
  registre solicitado, efetivo (ou `não informado pelo host`) e motivo. Continue com o
  padrão disponível, avisando que a preferência não foi aplicada. Não alegue economia
  nem seleção confirmada sem evidência do host; não eleve o modelo em resposta a falhas.
- Sem concorrência, execute as unidades em sequência. Sem delegação, aplique os papéis e
  convenções inline e registre o fallback. Nenhuma dessas limitações dispensa testes.

Se `sdd-builder` já estiver coordenando a sessão e o host impedir delegação aninhada,
ele aplica `feature-builder` na sessão atual e despacha os workers diretamente. Há um
único orquestrador da etapa 3. Se a restrição só for descoberta dentro de um subagente,
continue inline e informe a limitação; não abra outra árvore de agentes.

Os perfis do plugin preservam o formato de cada plataforma: Claude/Cursor usam
`model: inherit` no agente de testes; Copilot mantém seu frontmatter sem `model` e recebe
a seleção pela ferramenta quando disponível. A capacidade instalada é verificada em
tempo de execução. Referências oficiais: [Claude Code](https://code.claude.com/docs/en/sub-agents#choose-a-model),
[Cursor](https://cursor.com/docs/subagents) e
[Copilot CLI](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference).

## Decomposição da fase

O orquestrador mantém o quadro de unidades em memória/tarefas do host, sem criar mais
arquivos no projeto alvo. Não altere `plan.md` para acomodar o scheduler.

Cada unidade tem:

- `id`, feature, fase, `role`, objetivo e especialista da stack pertinente.
- `read_files`, `write_files` com caminhos concretos, `depends_on` e contratos de entrada
  e saída. Diretório amplo ou conjunto desconhecido não comprova independência.
- `resources`: build/cache, banco/schema, portas, simulador, fixtures e relatórios usados
  pelos comandos, incluindo caminhos gerados que não aparecem no Component Overview.
- Trechos relevantes de spec/plano, TC/ACs, convenções locais, comandos com cwd e critério
  de término. Encaminhe apenas o contexto necessário, sem histórico completo do chat.
- Estado `pending`, `running`, `completed`, `blocked` ou `failed`, modelo solicitado e
  efetivo, tentativas e retorno compacto.

Separe implementação e testes. `implementation` vai ao especialista da tecnologia;
`test-authoring` e `test-execution` vão ao `sdd-test-specialist`, acompanhados das
convenções de teste da stack. Arquivos de produção com testes embutidos não podem ter
dois escritores: autoria aguarda a implementação e recebe autorização explícita para
editar só a seção de teste, ou o orquestrador integra o teste em janela exclusiva.

Manifestos, lockfiles, registros DI, rotas globais, schemas, migrações, tipos públicos e
fixtures globais pertencem a unidades `integration` exclusivas, executadas antes ou
depois do lote paralelo conforme suas dependências. Estabilize primeiro os contratos
necessários. Não isole artificialmente passos que precisam decidir uma API juntos.

## Elegibilidade e despacho

Duas unidades só podem estar ativas juntas quando **todas** as condições forem verdade:

1. Estão na mesma fase e suas dependências estão concluídas e aceitas pelo orquestrador.
2. Seus conjuntos de escrita não se intersectam, e nenhum deles intersecta as leituras
   da outra unidade. Leitura de contrato estabilizado é permitida; leitura de arquivo
   ainda sendo escrito é dependência, mesmo sem edição concorrente.
3. Não alteram arquivos compartilhados/fundacionais e não disputam recursos mutáveis.
4. Seus comandos não varrem entradas que outro worker modifica. Build/teste do projeto
   inteiro fica na barreira da fase; checks locais só com escopo e recursos isolados.

Escolha um conjunto de unidades elegíveis até o limite efetivo e dispare as chamadas
concorrentes pela primitiva do host. Aguarde os retornos, inspecione os arquivos e os
contratos e então libere dependentes ou o próximo lote. Não cruze fronteiras de fases.
Se os slots estiverem ocupados, aguarde os workers ativos liberarem capacidade; não
reinicie chamadas rejeitadas em loop nem aumente o limite configurado para contornar o host.
Se a independência for incerta, una os passos em uma unidade ou serialize. Um grafo
cíclico exige replanejar o agrupamento, não aguardar indefinidamente.

Autoria de teste pode acompanhar a implementação somente quando usa contratos já
estabilizados e arquivos disjuntos, sem ler a implementação em edição. A execução desses
testes sempre depende da autoria **e** da implementação concluídas. No workspace
compartilhado, espere todos os escritores da fase antes de iniciar a validação integrada.
Paralelize comandos de teste nessa barreira apenas com isolamento comprovado de recursos.

Exemplo, com interfaces existentes e estáveis:

| Unidade | Papel | Escrita | Dependências |
| --- | --- | --- | --- |
| U1 | implementation | `src/parser.py` | nenhuma |
| U2 | implementation | `src/formatter.py` | nenhuma |
| U3 | test-authoring | `tests/test_parser.py` | nenhuma; recebe contrato estável |
| U4 | test-authoring | `tests/test_formatter.py` | nenhuma; recebe contrato estável |
| U5 | test-execution | nenhuma fonte | U1, U2, U3, U4; workspace estável |

Com três slots, U1/U2/U3 podem iniciar juntas; U4 entra no próximo lote. Se U3 precisar
ler `src/parser.py`, adicione U1 a `depends_on`, eliminando essa simultaneidade.

## Convergência, falhas e retomada

- Confira cada retorno contra `write_files` e a cobertura de TC/ACs. Uma unidade de autoria
  concluída entrega testes escritos, nunca evidência de que passaram.
- Pedido de ampliar escopo ou mudança de contrato: aguarde/pare os workers afetados,
  redefina as dependências e reenvie contexto mínimo. Não permita que o worker "aproveite"
  para corrigir arquivo pertencente a outra unidade.
- Falha de teste em produção volta ao worker de implementação; falha no teste volta à
  autoria. Reexecute os testes afetados e a validação integrada após qualquer correção.
  Retries usam o limite da fase; trocar worker ou modelo não zera esse limite.
- Conflito inesperado: pare e aguarde os workers envolvidos antes de editar; preserve o
  trabalho preexistente e os diffs válidos, reconcilie com um único escritor e valide
  novamente. Nunca faça reset/checkout/revert geral para "limpar" a concorrência.
- Cancelamento, timeout ou falha além do limite: pare novos despachos, encerre/aguarde
  todos os workers ativos e seus comandos antes de verificar, commitar ou reportar.
  Registre unidades pendentes/bloqueadas; não deixe writers órfãos.
- Retomada: reconstitua o quadro pelo plano e pelo estado real dos arquivos/commits.
  Preserve alterações não commitadas. Não trate retorno antigo de worker como aprovação
  do estado atual; revalide antes de concluir a fase.

Só o orquestrador executa stage, commit e escrita no roadmap. A fase inteira precisa
convergir e passar pela validação conjunta antes de receber seu commit.
