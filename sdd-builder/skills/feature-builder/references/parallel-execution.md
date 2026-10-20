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
| `implementation-model=inherit` ou `implementation-model=<ID>` | Escolha no plano inicial | Modelo de programação para unidades de implementação e integração, inclusive correções. |
| `test-model=inherit` ou `test-model=<ID>` | Escolha no plano inicial | Modelo dos workers de autoria e execução de testes, inclusive validações finais. |

Aceite equivalentes como `modo paralelo`, `sem paralelismo`, `no máximo 2 agentes`,
`Sol 6.1 para programação e Luna para testes` e `Sonnet 5.5 para programação e Haiku 5.5
para testes`. Resolva nomes/IDs no harness atual conforme [Seleção de modelos](model-selection.md).
`max-workers=1` serializa sem eliminar os contextos separados. Restrições explícitas
de não delegar/paralelizar prevalecem; em sequencial, o teto efetivo de workers é 1.

Opções inválidas/contraditórias de execução mantêm o padrão da opção afetada e são
registradas em Overrides ignored. Escolhas de **modelo** inválidas ou ambíguas voltam
à seleção pelo usuário; nunca aplique herança ou outro modelo como escolha implícita.

## Capacidade do host e seleção efetiva do modelo

Antes de iniciar a implementação, siga [Plano de execução e escolha de modelos por
harness](model-selection.md): identifique o harness e seu catálogo, apresente o plano com
as sugestões e resolva as escolhas de programação e testes. Não marque `in-progress`
nem despache workers enquanto faltar uma escolha necessária. Opções já informadas e
aplicáveis dispensam nova pergunta, mas o plano sempre é mostrado.

Aplique `implementation-model` em `implementation`/`integration` e `test-model` em
`test-authoring`/`test-execution`, com a ferramenta nativa de delegação e seu mecanismo
real de seleção. Perfis herdam o modelo; não há modelo de provedor fixo em agente algum.
Solicitado, ID resolvido e modelo efetivo são registrados separadamente. Um modelo
indisponível exige alternativa aceita, salvo fallback já autorizado pelo usuário.

Se `sdd-builder` já estiver coordenando a sessão e o host impedir delegação aninhada,
ele aplica `feature-builder` na sessão atual e despacha os workers diretamente. Há um
único orquestrador da etapa 3. Se a restrição só for descoberta dentro de um subagente,
reavalie com o usuário a execução inline e a herança de modelo quando diferirem do plano
aceito; não abra outra árvore de agentes nem dispense testes.

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
  resolvido/efetivo, tentativas e retorno compacto.

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
