# Plano de execução e escolha de modelos por harness

Contrato canônico da seleção de modelos na etapa de implementação. Execute depois de
carregar spec/plano/testes, conferir dependências e identificar as stacks, **antes** de
marcar `in-progress`, escrever código/testes ou despachar workers de implementação.

Os perfis do plugin usam `model: inherit` quando o formato aceita esse campo; nos demais
formatos, a herança é implícita. Nenhum especialista fixa provedor ou família de modelo.
Herança no perfil é um padrão técnico, não uma escolha já feita pelo usuário.

## 1. Identificar harness e capacidades

Detecte o ambiente pela identificação fornecida pela sessão, metadados das ferramentas
e configuração local relevante. Não deduza o harness a partir do modelo da conversa:
um modelo Claude pode estar no Cursor, Codex ou Antigravity. A presença de `.claude/`,
`.cursor/` ou `.codex/` no repositório também não comprova qual harness está ativo.

Consulte, nesta ordem:

1. Catálogo/enum de modelos e capacidades expostos pelas ferramentas da sessão.
2. Se necessário, comandos de consulta documentados para o harness instalado e seus
   perfis existentes. Leia apenas configuração necessária, sem expor credenciais.
3. Documentação oficial para esclarecer nomes e mecanismos, nunca como prova de que
   aquela conta tem acesso a um modelo.

Registre nome/variante do harness, fonte da identificação, delegação, concorrência,
limite de profundidade e mecanismo de seleção: por chamada, por perfil ou só sessão.
Confira se a escolha de modelo exige contexto novo ou outro parâmetro nativo. Use o
schema real da ferramenta; não crie uma chamada universal fictícia.

Se a identificação for ambígua, apresente `harness não identificado` e peça o dado que
falta junto da escolha de modelos. Não invente comandos, catálogos ou IDs para contornar
a falta de descoberta. Codex, Claude Code, Cursor, Antigravity e Copilot podem expor
capacidades diferentes conforme versão, superfície, conta e configuração.

## 2. Preparar sugestões e opções

Prefira as combinações abaixo **quando os modelos e a seleção por papel estiverem
disponíveis no harness atual**. São sugestões de produto, não modelos fixos nos perfis
nem uma avaliação de desempenho ou preço válida para qualquer projeto.

| Harness | Programação (`implementation-model`) | Testes (`test-model`) |
| --- | --- | --- |
| Codex | GPT-6.1 Sol | GPT-6 Luna |
| Claude Code | Claude Sonnet 5.5 | Claude Haiku 5.5 |
| Cursor | Claude Sonnet 5.5 | Claude Haiku 5.5 |
| Antigravity | Modelo de programação entre os disponíveis na sessão | Modelo mais leve entre os disponíveis para esse papel |
| Copilot ou outro harness | Modelo de programação do catálogo atual | Modelo mais leve do catálogo atual, ou herdar se não houver alternativa |

Para Antigravity e outros harnesses, apresente nomes concretos após consultar o catálogo,
com justificativa curta baseada nas descrições disponíveis. Se não houver evidência
para comparar capacidade/custo, mostre as opções sem rotulá-las como "menor"/"melhor".

Resolva nome de apresentação → ID exato aceito pelo harness. Por exemplo, `gpt-6.1-sol`
e `gpt-6-luna` podem ser usados no Codex **se constarem no catálogo da sessão**. IDs da
API Claude, como `claude-sonnet-5-5` e `claude-haiku-5-5`, não devem ser copiados para o
Cursor ou outro harness sem confirmar seu mapeamento. `sonnet` e `haiku` não garantem
versão 5.5; não substitua uma versão solicitada por um alias móvel sem informar.

Se uma sugestão não estiver disponível, mostre isso e ofereça opções reais, incluindo
`inherit` quando suportado. Não selecione automaticamente outra versão ou provedor.
Sem catálogo consultável, marque disponibilidade como `não verificada`, peça um ID
reconhecido pelo usuário ou ofereça herança; não execute trabalho para sondar um modelo.

## 3. Apresentar plano e recolher a escolha

Prepare um plano concreto e curto a partir de `plan.md`, sem o reescrever. Mostre:

- Feature, fases e principais unidades; especialistas responsáveis e dependências.
- O que pode rodar em paralelo, integrações exclusivas e validações de cada fase.
- Harness detectado, modo efetivo, limite de workers e eventuais limitações.
- Duas escolhas independentes: programação e testes, com sugestão, ID resolvido,
  disponibilidade e alternativas. `implementation-model` cobre `implementation` e
  `integration`; `test-model` cobre `test-authoring` e `test-execution`, inclusive retries
  e verificação final. Nenhum deles troca o modelo da sessão do orquestrador.

Exemplo de apresentação, quando o catálogo do Codex confirmar os IDs:

```text
Plano de implementação: F03
Harness: Codex | Execução: parallel | Máximo de workers: 3
Fase 1: contratos e registros, em sequência.
Fase 2: U1 serviço e U2 testes de contrato em paralelo; U3 execução aguarda ambos.
Fase 3: integração, suíte completa e conferência dos critérios de aceite.

Programação: GPT-6.1 Sol (gpt-6.1-sol), recomendado, disponível.
Testes: GPT-6 Luna (gpt-6-luna), recomendado, disponível.
Alternativas: herdar o modelo da sessão ou escolher outros IDs do catálogo exibido.
Seleção: aguardando escolha do usuário.
```

Ofereça "Usar as recomendações", "Herdar o modelo da sessão nos dois papéis" e
"Escolher por papel", usando a interface de pergunta disponível no harness ou o chat.
Ao escolher por papel, liste os modelos disponíveis e peça somente os valores faltantes.
Explique que a resposta define os LLMs usados na implementação; não repita a pergunta
como uma autorização genérica para executar um trabalho já solicitado.

Regras de precedência:

1. Escolhas explícitas na invocação ou já aceitas nesta execução têm prioridade sobre
   sugestões. Valide-as e inclua-as no plano; não peça confirmação de novo.
2. Se os dois papéis já estiverem definidos e aplicáveis, apresente o plano e prossiga.
   Se apenas um foi definido, pergunte somente pelo outro.
3. "Use as recomendações" autoriza a dupla sugerida disponível; "herde nos dois" define
   ambos como `inherit`. Se a dupla recomendada estiver indisponível, peça a escolha da
   alternativa, sem interpretar a frase como autorização para qualquer substituição.
4. Na ausência de escolha, aguarde a resposta. Opção preselecionada, silêncio, timeout
   ou a autonomia padrão da skill não contam como resposta. Sem interação, devolva o
   plano com seleção pendente e os parâmetros necessários, sem iniciar a implementação.

Enquanto aguarda, apenas prepare leituras e decomposição de tarefas. Não despache workers,
altere arquivos do projeto ou marque início no roadmap. Esta escolha ocorre uma vez por
execução, não por fase ou por unidade. Preserve a decisão em memória/tarefas da sessão;
na retomada, reutilize-a se ainda houver evidência da escolha e das mesmas capacidades.

## 4. Aplicar a decisão sem alterar o ambiente global

- Use o modelo selecionado na chamada de **cada** worker, respeitando seu papel, inclusive
  retries e correções finais. A integração de código usa `implementation-model`.
- Prefira override nativo por chamada. Se o host só aceitar modelo por perfil, use um
  perfil existente que combine o contrato do worker com a escolha aceita. Não use um
  perfil genérico de menor custo que perca as instruções e o escopo da unidade.
- `inherit` usa o mecanismo de herança do host, não um ID literal quando ele não o
  reconhecer. A identidade do agente ou o texto do prompt não comprovam seleção de LLM.
- Não reescreva perfis compartilhados, plugin instalado ou configuração global durante
  a execução. Não troque o modelo do orquestrador para simular seleção por worker.
- Se o host só suportar um modelo por sessão ou não permitir delegação, mostre a limitação
  no plano. Ofereça execução inline/sequencial com o modelo da sessão ou ajuste manual
  pelo usuário antes de continuar. `sem subagentes` torna a seleção por worker inaplicável;
  se a instrução não trouxer escolhas incompatíveis, informe herança efetiva e prossiga
  com a execução inline já solicitada, sem uma pergunta inútil.

Sem suporte à seleção escolhida, não faça fallback silencioso nem continue apenas com
um aviso. Peça uma alternativa aplicável, salvo se o usuário já autorizou explicitamente
esse fallback. Registre essa autorização por papel. Uma substituição imposta pelo host
durante a execução exige parar novos despachos afetados, aguardar/encerrar esses workers,
preservar os diffs e obter nova escolha antes de continuar. Não reinicie o orçamento de
retries. Falhas de teste não autorizam aumentar o modelo automaticamente.

No relatório e nos retornos das unidades, diferencie modelo **solicitado**, **resolvido**
para despacho e **efetivo** informado pelo host. Se o efetivo não for exposto, escreva
`não informado pelo host`; não deduza que a escolha foi aplicada nem anuncie economia.

## Referências oficiais

- [Modelos OpenAI](https://developers.openai.com/api/docs/models) e [subagentes no Codex](https://learn.chatgpt.com/docs/agent-configuration/subagents).
- [Claude Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview), [Claude Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview) e [seleção em subagentes Claude Code](https://code.claude.com/docs/en/sub-agents#choose-a-model).
- [Subagentes Cursor](https://cursor.com/docs/subagents).
- [Modelos Antigravity](https://www.antigravity.google/docs/models/) e [consulta de modelos na CLI](https://www.antigravity.google/docs/cli/headless/).
- [Referência Copilot CLI](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference).
