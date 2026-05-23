---
name: dispatch-experts
description: Itera sobre o INDEX.md dos relatórios e invoca um especialista por relatório, na ordem do índice, aguardando o fix.md de cada um antes de prosseguir.
---

# Skill: dispatch-experts

Lê `.sonar-reports/reports/INDEX.md` e, para cada relatório listado, invoca o especialista recomendado passando o caminho do relatório como input. **Um especialista por relatório.**

## Modelo de orquestração

Dentro de **uma sessão única do Copilot CLI**, o despacho é **sequencial**: o agente `@sonar-code-cleaner` chama o especialista A, aguarda a criação do `REPORT-XXX.fix.md`, depois chama o especialista B. Isso é feito assim porque agentes sub-invocados na mesma sessão compartilham contexto e não rodam realmente em paralelo.

Para **paralelismo real**, oriente o usuário a usar a modalidade `--multi-session` (se a versão do Copilot CLI suportar) ou abrir terminais separados — uma sessão por relatório, cada uma invocando seu especialista. Os relatórios são independentes por design (um arquivo por relatório), então não há conflito.

## Inputs

- `.sonar-reports/reports/INDEX.md` (gerado por `generate-issue-reports`)
- Diretório `.sonar-reports/reports/` com os REPORT-*.md

## Passos

1. **Ler o INDEX.md** e parsear a tabela de relatórios.

2. **Para cada linha do índice (na ordem listada):**

   a. **Anunciar** ao usuário qual especialista será invocado:
      ```
      [3/7] REPORT-003-src__api__users.md
          • Arquivo: src/api/users.py
          • 8 issues (2 HIGH, 5 MEDIUM, 1 LOW) — taxonomia Clean Code
          • Despachando @python-expert...
      ```

   b. **Invocar o agente** especialista passando o caminho do relatório.
      No estilo do Copilot CLI, o orquestrador pode delegar com:
      ```
      @<recommended_agent> Por favor, resolva o relatório
      .sonar-reports/reports/REPORT-003-src__api__users.md
      seguindo o contrato definido no seu prompt.
      ```

   c. **Aguardar** a presença do arquivo `REPORT-003-src__api__users.fix.md` no mesmo diretório.

   d. **Ler o status** do fix report (`resolved` / `partial` / `needs-human-review`) e logar:
      ```
          ✓ @python-expert concluiu — status: resolved (8/8 issues)
      ```

   e. **Se `needs-human-review`:** registrar para o SUMMARY, mas não bloquear o pipeline.

3. **Ao final**, gravar um log consolidado em `.sonar-reports/dispatch.log` com a sequência de invocações, tempos (se medidos), e status de cada despacho.

## Saída

- N arquivos `REPORT-<NNN>-<slug>.fix.md` (criados pelos especialistas)
- 1 arquivo `.sonar-reports/dispatch.log`
- Resumo textual ao orquestrador.

## Modo multi-sessão (instrução para o usuário)

Se o usuário quiser paralelizar de verdade, instrua-o assim:

> Para processar em paralelo, abra `N` terminais e em cada um execute:
>
> ```bash
> copilot
> > @python-expert resolva .sonar-reports/reports/REPORT-003-src__api__users.md
> ```
>
> Como cada relatório toca um arquivo distinto, não há risco de conflito de edição.
> Quando todos os fix reports estiverem em disco, rode novamente o orquestrador e ele
> pulará direto para a fase de consolidação.

## Tratamento de erros

| Erro                                       | Ação                                                                            |
| ------------------------------------------ | ------------------------------------------------------------------------------- |
| INDEX.md ausente                           | Pedir para rodar `generate-issue-reports` antes                                 |
| Especialista não responde / não cria `.fix.md` | Logar timeout, marcar como `dispatch-failed`, seguir para o próximo            |
| Especialista mapeado não existe no plugin  | Cair para `@generic-expert` automaticamente e avisar                            |
| Mesmo relatório sendo processado 2x        | Detectar pela existência de `.fix.md` recente e pular                           |
