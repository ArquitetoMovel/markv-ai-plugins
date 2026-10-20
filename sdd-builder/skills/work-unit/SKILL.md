---
name: work-unit
description: >
  Executa uma unidade delimitada de implementação, integração, autoria ou execução de
  testes delegada pelo feature-builder. Define escopo de arquivos, contexto mínimo,
  dependências e retorno com evidências. Usada pelos especialistas do fluxo SDD.
---

# Unidade de trabalho SDD

Execute somente a unidade recebida do `sdd-feature-builder`. Esta skill é o contrato
dos workers; não execute o fluxo do orquestrador nem carregue a skill `feature-builder`.

## Entrada obrigatória

- ID da unidade, feature, fase, papel e objetivo verificável.
- Raiz do projeto e pasta da feature em caminhos absolutos.
- `read_files`: arquivos necessários para consulta; `write_files`: lista exata de
  arquivos que pode criar ou alterar. Lista vazia significa nenhuma edição de fonte.
- `depends_on`: unidades concluídas das quais esta depende e os contratos estabilizados.
- Trechos relevantes da spec, passos do plano, casos de teste e critérios de aceite
  com seus IDs. Sem `tests.md`, expectativas derivadas da estratégia de testes da spec.
- Convenções aplicáveis do projeto e da stack, comandos autorizados, diretório de
  execução e recursos exclusivos concedidos (build, banco, porta, simulador, fixtures).
- Critério de término, harness, modelo solicitado pelo usuário, ID resolvido para
  despacho, fallbacks já autorizados e orçamento de tentativas restante. Programação/integração recebem
  `implementation-model`; autoria/execução de testes recebem `test-model`.

Se faltar escopo, contrato ou dependência necessária, devolva `blocked` com a informação
que falta. Não invente uma interface nem amplie o escopo por conta própria.

## Papéis

| Papel | Responsabilidade | Limite |
| --- | --- | --- |
| `implementation` | Implementar o código de produção da unidade conforme o contrato. | Não criar ou modificar testes atribuídos a outro worker. |
| `integration` | Ajustar contratos, registros, manifestos, migrações ou fixtures compartilhadas. | Só executar na janela exclusiva concedida pelo orquestrador. |
| `test-authoring` | Criar testes rastreáveis aos casos/ACs, inclusive fronteiras e erros previstos. | Editar somente os arquivos de teste autorizados; não corrigir produção. |
| `test-execution` | Executar comandos e coletar resultados do estado integrado e estável. | Não editar fontes, testes ou snapshots; artefatos gerados ficam nos diretórios autorizados. |

Autoria não comprova aprovação: um teste escrito fica `pending` até a execução real
contra a implementação concluída. Não execute testes enquanto algum worker altera os
arquivos lidos pelo comando. Comandos de build/teste podem gerar caches, relatórios e
objetos no banco; respeite os recursos reservados mesmo sem editar código.

## Contexto e execução

1. Leia os trechos recebidos e os arquivos necessários à unidade. Consulte instruções
   locais aplicáveis, incluindo `AGENTS.md` e `CLAUDE.md`; não presuma que o host as herdou.
2. Preserve alterações preexistentes e o trabalho dos demais workers. Precisou de outro
   arquivo, fixture global, dependência ou contrato diferente? Pare e devolva `blocked`
   com o ajuste proposto para o orquestrador reagendar.
3. Cumpra seu papel. As convenções e comandos da stack são referências, não autorização
   para instalar dependências, rodar a suíte inteira ou formatar arquivos fora do escopo.
   Só execute os comandos concedidos quando os recursos e entradas estiverem estáveis.
4. Retorne evidências curtas. Em falha, inclua o comando reproduzível e o trecho relevante
   do erro. Não despeje logs completos ou copie a spec inteira para o retorno.

Não carregue PRD completo, histórico do chat, outras fases, roadmap ou instruções de
orquestração. Não abra novos subagentes. Um contexto novo por unidade evita acumular o
histórico das outras unidades; retries recebem apenas o contrato e o erro necessários.

## Testes e falhas

- Use o framework e os comandos existentes no projeto. Preserve os resultados esperados
  de `tests.md`; não enfraqueça asserções, desative casos ou atualize snapshots para
  esconder uma falha. Stubs de serviços só em código de teste, quando autorizados.
- Falha do produto volta ao especialista de implementação, por meio do orquestrador.
  Falha no teste volta à autoria, em nova unidade com escopo explícito.
- Informe saída diferente de zero, teste não coletado, caso pulado e recurso ausente
  separadamente. Zero testes executados não comprova os casos atribuídos.
- Não declare falha preexistente sem evidência anterior à alteração; o orquestrador
  decide a classificação final e controla o limite de retries entre workers.
- O worker não escolhe nem troca seu próprio modelo. Repita o modelo informado pelo host
  quando disponível; caso contrário, escreva `não informado pelo host`, sem inferir pela
  identidade do agente ou pelo texto do prompt. Se o host informar substituição em
  relação ao ID resolvido sem fallback autorizado, devolva `blocked` antes de editar/executar
  para o orquestrador resolver a divergência. Com fallback autorizado, registre solicitado,
  resolvido e efetivo; não interprete herança do perfil como autorização de fallback.

## Retorno obrigatório

```text
Unidade: <ID> | Feature: <ID> | Fase: <nome> | Papel: <papel>
Status: completed | blocked | failed
Harness: <nome>
Modelo solicitado: <nome/inherit/ID> | Resolvido: <herança ou ID do harness>
Modelo efetivo: <ID ou não informado pelo host>
Arquivos criados/modificados: <lista exata ou nenhum>
Contratos entregues: <assinaturas/exports relevantes>
Comandos: <diretório, comando, código de saída, resumo ou não executado e motivo>
Casos/ACs: <TC -> AC -> arquivo::teste -> passed/failed/skipped/pending>
Falhas e bloqueios: <reprodução curta e dependência necessária>
Desvios: <o que mudou e por quê>
Pendências para integração: <lista ou nenhuma>
```

`completed` significa apenas que o papel da unidade terminou. Não significa que a fase
passou, que o critério de aceite foi satisfeito ou que a feature pode virar `done`.

Nunca faça stage, commit, reset, troca de branch ou escrita no roadmap, PRD, `spec.md`,
`plan.md` e `tests.md`. A integração, a aprovação da fase e o progresso pertencem ao
`sdd-feature-builder`.
